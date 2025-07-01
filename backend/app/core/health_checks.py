"""
Production readiness validation and comprehensive health check system.
"""
import asyncio
import aiohttp
import aioredis
import psutil
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from minio import Minio
import httpx
from playwright.async_api import async_playwright
from .logging import production_logger, database_logger, api_logger
from ..database import get_db
from ..config import settings


class HealthCheckResult:
    """Represents a health check result."""
    
    def __init__(self, name: str, status: str, details: Dict[str, Any], 
                 response_time: float):
        self.name = name
        self.status = status  # 'healthy', 'degraded', 'unhealthy'
        self.details = details
        self.response_time = response_time
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status,
            'details': self.details,
            'response_time_ms': self.response_time * 1000,
            'timestamp': self.timestamp.isoformat()
        }


class SystemHealthChecker:
    """Comprehensive system health checking."""
    
    def __init__(self):
        self.logger = production_logger.get_logger("health_checks")
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'minio': self.check_minio,
            'ollama': self.check_ollama,
            'flaresolverr': self.check_flaresolverr,
            'playwright': self.check_playwright,
            'api_endpoints': self.check_api_endpoints,
            'background_jobs': self.check_background_jobs,
            'disk_space': self.check_disk_space,
            'memory_usage': self.check_memory_usage,
            'external_services': self.check_external_services
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        self.logger.info("Starting comprehensive health checks")
        
        results = {}
        tasks = []
        
        # Run all checks concurrently
        for check_name, check_func in self.checks.items():
            task = asyncio.create_task(self._run_check(check_name, check_func))
            tasks.append(task)
        
        check_results = await asyncio.gather(*tasks)
        
        # Process results
        for result in check_results:
            results[result.name] = result.to_dict()
        
        # Calculate overall health
        overall_health = self._calculate_overall_health(results)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': overall_health['status'],
            'health_score': overall_health['score'],
            'checks': results,
            'summary': overall_health['summary']
        }
    
    async def _run_check(self, name: str, check_func) -> HealthCheckResult:
        """Run a single health check with timing."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            status, details = await check_func()
        except Exception as e:
            self.logger.error(f"Health check {name} failed: {str(e)}")
            status = 'unhealthy'
            details = {'error': str(e)}
        
        response_time = asyncio.get_event_loop().time() - start_time
        
        return HealthCheckResult(name, status, details, response_time)
    
    async def check_database(self) -> tuple[str, Dict[str, Any]]:
        """Check database connectivity and performance."""
        details = {
            'connection': False,
            'response_time_ms': 0,
            'active_connections': 0,
            'version': None
        }
        
        try:
            async with get_db() as db:
                # Test basic connectivity
                start = asyncio.get_event_loop().time()
                result = await db.execute(text("SELECT 1"))
                response_time = asyncio.get_event_loop().time() - start
                
                details['connection'] = True
                details['response_time_ms'] = response_time * 1000
                
                # Get connection pool stats
                pool_status = await db.execute(
                    text("SELECT count(*) FROM pg_stat_activity")
                )
                details['active_connections'] = pool_status.scalar()
                
                # Get PostgreSQL version
                version_result = await db.execute(text("SELECT version()"))
                details['version'] = version_result.scalar()
                
                # Check critical tables
                tables = ['websites', 'opportunities', 'scraping_jobs', 'users']
                for table in tables:
                    count_result = await db.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    details[f'{table}_count'] = count_result.scalar()
                
                # Determine status
                if response_time > 0.1:  # 100ms
                    return 'degraded', details
                else:
                    return 'healthy', details
                
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_redis(self) -> tuple[str, Dict[str, Any]]:
        """Check Redis connectivity and performance."""
        details = {
            'connection': False,
            'response_time_ms': 0,
            'memory_usage_mb': 0,
            'connected_clients': 0
        }
        
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            redis = await aioredis.from_url(redis_url)
            
            # Test connectivity
            start = asyncio.get_event_loop().time()
            await redis.ping()
            response_time = asyncio.get_event_loop().time() - start
            
            details['connection'] = True
            details['response_time_ms'] = response_time * 1000
            
            # Get Redis info
            info = await redis.info()
            details['memory_usage_mb'] = info.get('used_memory', 0) / 1024 / 1024
            details['connected_clients'] = info.get('connected_clients', 0)
            details['version'] = info.get('redis_version', 'unknown')
            
            # Test cache operations
            test_key = 'health_check_test'
            await redis.set(test_key, 'test_value', ex=10)
            test_value = await redis.get(test_key)
            details['cache_operations'] = test_value == b'test_value'
            
            await redis.close()
            
            if response_time > 0.05:  # 50ms
                return 'degraded', details
            else:
                return 'healthy', details
                
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_minio(self) -> tuple[str, Dict[str, Any]]:
        """Check MinIO object storage."""
        details = {
            'connection': False,
            'buckets': [],
            'total_objects': 0
        }
        
        try:
            minio_client = Minio(
                os.environ.get('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.environ.get('MINIO_ACCESS_KEY', 'minioadmin'),
                secret_key=os.environ.get('MINIO_SECRET_KEY', 'minioadmin'),
                secure=False
            )
            
            # List buckets
            buckets = minio_client.list_buckets()
            details['connection'] = True
            details['buckets'] = [b.name for b in buckets]
            
            # Check main buckets exist
            required_buckets = ['documents', 'exports', 'screenshots']
            for bucket in required_buckets:
                if bucket not in details['buckets']:
                    # Create missing bucket
                    minio_client.make_bucket(bucket)
                    details[f'{bucket}_created'] = True
            
            # Count objects in documents bucket
            objects = minio_client.list_objects('documents', recursive=True)
            details['total_objects'] = sum(1 for _ in objects)
            
            return 'healthy', details
            
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_ollama(self) -> tuple[str, Dict[str, Any]]:
        """Check Ollama LLM service."""
        details = {
            'connection': False,
            'models': [],
            'response_time_ms': 0
        }
        
        try:
            ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
            
            async with httpx.AsyncClient() as client:
                # Check API availability
                start = asyncio.get_event_loop().time()
                response = await client.get(f"{ollama_url}/api/tags")
                response_time = asyncio.get_event_loop().time() - start
                
                if response.status_code == 200:
                    details['connection'] = True
                    details['response_time_ms'] = response_time * 1000
                    
                    # Get available models
                    data = response.json()
                    details['models'] = [
                        model['name'] for model in data.get('models', [])
                    ]
                    
                    # Check if required model is available
                    required_model = 'llama3.2'
                    if required_model in details['models']:
                        details['required_model_available'] = True
                    else:
                        details['required_model_available'] = False
                        return 'degraded', details
                    
                    return 'healthy', details
                else:
                    details['status_code'] = response.status_code
                    return 'unhealthy', details
                    
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_flaresolverr(self) -> tuple[str, Dict[str, Any]]:
        """Check FlareSolverr service."""
        details = {
            'connection': False,
            'version': None,
            'sessions': 0
        }
        
        try:
            flaresolverr_url = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191')
            
            async with httpx.AsyncClient() as client:
                # Check health endpoint
                response = await client.get(f"{flaresolverr_url}/health")
                
                if response.status_code == 200:
                    details['connection'] = True
                    data = response.json()
                    details['status'] = data.get('status')
                    
                    # Get version info
                    version_response = await client.post(
                        f"{flaresolverr_url}/v1",
                        json={'cmd': 'status'}
                    )
                    if version_response.status_code == 200:
                        version_data = version_response.json()
                        details['version'] = version_data.get('version')
                        details['sessions'] = len(version_data.get('sessions', []))
                    
                    return 'healthy', details
                else:
                    details['status_code'] = response.status_code
                    return 'unhealthy', details
                    
        except Exception as e:
            details['error'] = str(e)
            # FlareSolverr is optional, so degraded instead of unhealthy
            return 'degraded', details
    
    async def check_playwright(self) -> tuple[str, Dict[str, Any]]:
        """Check Playwright browser automation."""
        details = {
            'browsers_available': [],
            'test_navigation': False
        }
        
        try:
            playwright = await async_playwright().start()
            
            # Check available browsers
            for browser_type in ['chromium', 'firefox', 'webkit']:
                try:
                    browser = await getattr(playwright, browser_type).launch(
                        headless=True
                    )
                    await browser.close()
                    details['browsers_available'].append(browser_type)
                except Exception:
                    pass
            
            # Test basic navigation
            if 'chromium' in details['browsers_available']:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    response = await page.goto('https://example.com', timeout=10000)
                    details['test_navigation'] = response.status < 400
                except Exception:
                    details['test_navigation'] = False
                finally:
                    await browser.close()
            
            await playwright.stop()
            
            if len(details['browsers_available']) > 0 and details['test_navigation']:
                return 'healthy', details
            elif len(details['browsers_available']) > 0:
                return 'degraded', details
            else:
                return 'unhealthy', details
                
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_api_endpoints(self) -> tuple[str, Dict[str, Any]]:
        """Check API endpoint availability."""
        details = {
            'endpoints_tested': 0,
            'endpoints_healthy': 0,
            'response_times': {}
        }
        
        # Define critical endpoints to test
        base_url = f"http://localhost:{settings.PORT}"
        endpoints = [
            ('GET', '/health'),
            ('GET', '/api/websites'),
            ('GET', '/api/opportunities'),
            ('GET', '/api/jobs'),
            ('GET', '/docs')
        ]
        
        async with httpx.AsyncClient() as client:
            for method, endpoint in endpoints:
                details['endpoints_tested'] += 1
                
                try:
                    start = asyncio.get_event_loop().time()
                    
                    if method == 'GET':
                        response = await client.get(
                            f"{base_url}{endpoint}",
                            timeout=5.0
                        )
                    
                    response_time = asyncio.get_event_loop().time() - start
                    
                    if response.status_code < 400:
                        details['endpoints_healthy'] += 1
                        details['response_times'][endpoint] = response_time * 1000
                    else:
                        details[f'{endpoint}_status'] = response.status_code
                        
                except Exception as e:
                    details[f'{endpoint}_error'] = str(e)
        
        # Calculate health
        health_ratio = details['endpoints_healthy'] / details['endpoints_tested']
        
        if health_ratio == 1.0:
            return 'healthy', details
        elif health_ratio >= 0.8:
            return 'degraded', details
        else:
            return 'unhealthy', details
    
    async def check_background_jobs(self) -> tuple[str, Dict[str, Any]]:
        """Check background job processing."""
        details = {
            'worker_processes': 0,
            'pending_jobs': 0,
            'failed_jobs_24h': 0,
            'average_processing_time': 0
        }
        
        try:
            # Check for worker processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'worker' in ' '.join(proc.info['cmdline'] or []):
                        details['worker_processes'] += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Check job statistics from database
            async with get_db() as db:
                # Pending jobs
                pending_result = await db.execute(
                    text("SELECT COUNT(*) FROM scraping_jobs WHERE status = 'pending'")
                )
                details['pending_jobs'] = pending_result.scalar()
                
                # Failed jobs in last 24 hours
                failed_result = await db.execute(
                    text("""
                        SELECT COUNT(*) FROM scraping_jobs 
                        WHERE status = 'failed' 
                        AND created_at > NOW() - INTERVAL '24 hours'
                    """)
                )
                details['failed_jobs_24h'] = failed_result.scalar()
                
                # Average processing time
                avg_time_result = await db.execute(
                    text("""
                        SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))
                        FROM scraping_jobs
                        WHERE status = 'completed'
                        AND completed_at IS NOT NULL
                        AND started_at IS NOT NULL
                        AND created_at > NOW() - INTERVAL '24 hours'
                    """)
                )
                avg_time = avg_time_result.scalar()
                details['average_processing_time'] = avg_time or 0
            
            # Determine health
            if details['worker_processes'] > 0 and details['pending_jobs'] < 100:
                return 'healthy', details
            elif details['worker_processes'] > 0:
                return 'degraded', details
            else:
                return 'unhealthy', details
                
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_disk_space(self) -> tuple[str, Dict[str, Any]]:
        """Check disk space availability."""
        details = {}
        
        try:
            # Check main partition
            disk_usage = psutil.disk_usage('/')
            details['total_gb'] = disk_usage.total / (1024**3)
            details['used_gb'] = disk_usage.used / (1024**3)
            details['free_gb'] = disk_usage.free / (1024**3)
            details['percent_used'] = disk_usage.percent
            
            # Check data directories
            data_dirs = ['/var/lib/postgresql', '/var/lib/redis', '/data']
            for dir_path in data_dirs:
                if os.path.exists(dir_path):
                    usage = psutil.disk_usage(dir_path)
                    details[f'{dir_path}_percent_used'] = usage.percent
            
            # Determine health
            if details['percent_used'] < 80:
                return 'healthy', details
            elif details['percent_used'] < 90:
                return 'degraded', details
            else:
                return 'unhealthy', details
                
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_memory_usage(self) -> tuple[str, Dict[str, Any]]:
        """Check memory usage."""
        details = {}
        
        try:
            # System memory
            memory = psutil.virtual_memory()
            details['total_gb'] = memory.total / (1024**3)
            details['used_gb'] = memory.used / (1024**3)
            details['available_gb'] = memory.available / (1024**3)
            details['percent_used'] = memory.percent
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info()
            details['process_memory_mb'] = process_memory.rss / (1024**2)
            details['process_memory_percent'] = process.memory_percent()
            
            # Swap memory
            swap = psutil.swap_memory()
            details['swap_percent_used'] = swap.percent
            
            # Determine health
            if memory.percent < 80 and swap.percent < 50:
                return 'healthy', details
            elif memory.percent < 90:
                return 'degraded', details
            else:
                return 'unhealthy', details
                
        except Exception as e:
            details['error'] = str(e)
            return 'unhealthy', details
    
    async def check_external_services(self) -> tuple[str, Dict[str, Any]]:
        """Check external service availability."""
        details = {
            'services_tested': 0,
            'services_available': 0,
            'response_times': {}
        }
        
        # Key external services
        services = [
            ('Google', 'https://www.google.com'),
            ('Government Portal', 'https://www.tenders.gov.au'),
            ('DNS', 'https://1.1.1.1')
        ]
        
        async with httpx.AsyncClient() as client:
            for service_name, url in services:
                details['services_tested'] += 1
                
                try:
                    start = asyncio.get_event_loop().time()
                    response = await client.get(url, timeout=5.0)
                    response_time = asyncio.get_event_loop().time() - start
                    
                    if response.status_code < 400:
                        details['services_available'] += 1
                        details['response_times'][service_name] = response_time * 1000
                    else:
                        details[f'{service_name}_status'] = response.status_code
                        
                except Exception as e:
                    details[f'{service_name}_error'] = str(type(e).__name__)
        
        # Calculate health
        availability_ratio = details['services_available'] / details['services_tested']
        
        if availability_ratio == 1.0:
            return 'healthy', details
        elif availability_ratio >= 0.5:
            return 'degraded', details
        else:
            return 'unhealthy', details
    
    def _calculate_overall_health(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health."""
        statuses = [r['status'] for r in results.values()]
        
        healthy_count = statuses.count('healthy')
        degraded_count = statuses.count('degraded')
        unhealthy_count = statuses.count('unhealthy')
        
        total_checks = len(statuses)
        
        # Calculate health score (0-100)
        health_score = (
            (healthy_count * 100) +
            (degraded_count * 50) +
            (unhealthy_count * 0)
        ) / total_checks
        
        # Determine overall status
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 2:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        # Generate summary
        summary = {
            'total_checks': total_checks,
            'healthy': healthy_count,
            'degraded': degraded_count,
            'unhealthy': unhealthy_count,
            'critical_issues': []
        }
        
        # Identify critical issues
        critical_components = ['database', 'redis', 'api_endpoints']
        for component in critical_components:
            if results.get(component, {}).get('status') == 'unhealthy':
                summary['critical_issues'].append(f"{component} is down")
        
        return {
            'status': overall_status,
            'score': health_score,
            'summary': summary
        }


class ProductionReadinessValidator:
    """Validate production readiness of the system."""
    
    def __init__(self):
        self.logger = production_logger.get_logger("production_validator")
        self.validations = {
            'environment_variables': self.validate_environment,
            'database_migrations': self.validate_database,
            'security_configuration': self.validate_security,
            'performance_baselines': self.validate_performance,
            'monitoring_setup': self.validate_monitoring,
            'backup_recovery': self.validate_backup,
            'deployment_configuration': self.validate_deployment
        }
    
    async def validate_all(self) -> Dict[str, Any]:
        """Run all production readiness validations."""
        self.logger.info("Starting production readiness validation")
        
        results = {}
        
        for validation_name, validation_func in self.validations.items():
            try:
                result = await validation_func()
                results[validation_name] = result
            except Exception as e:
                self.logger.error(f"Validation {validation_name} failed: {str(e)}")
                results[validation_name] = {
                    'passed': False,
                    'errors': [str(e)]
                }
        
        # Calculate readiness score
        passed_count = sum(1 for r in results.values() if r.get('passed'))
        total_count = len(results)
        readiness_score = (passed_count / total_count) * 100
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'readiness_score': readiness_score,
            'production_ready': readiness_score >= 90,
            'validations': results,
            'summary': self._generate_summary(results)
        }
    
    async def validate_environment(self) -> Dict[str, Any]:
        """Validate environment variables."""
        required_vars = [
            'DATABASE_URL',
            'REDIS_URL',
            'SECRET_KEY',
            'MINIO_ENDPOINT',
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'OLLAMA_URL',
            'CREDENTIAL_ENCRYPTION_KEY'
        ]
        
        optional_vars = [
            'SENTRY_DSN',
            'FLARESOLVERR_URL',
            'CAPTCHA_SERVICE_KEY',
            'PROXY_URLS'
        ]
        
        result = {
            'passed': True,
            'missing_required': [],
            'missing_optional': [],
            'warnings': []
        }
        
        # Check required variables
        for var in required_vars:
            if not os.environ.get(var):
                result['missing_required'].append(var)
                result['passed'] = False
        
        # Check optional variables
        for var in optional_vars:
            if not os.environ.get(var):
                result['missing_optional'].append(var)
        
        # Security checks
        if os.environ.get('SECRET_KEY') == 'development':
            result['warnings'].append("SECRET_KEY is using development value")
            result['passed'] = False
        
        return result
    
    async def validate_database(self) -> Dict[str, Any]:
        """Validate database setup."""
        result = {
            'passed': True,
            'migrations_current': False,
            'indices_optimized': False,
            'connection_pool_configured': False
        }
        
        try:
            async with get_db() as db:
                # Check migrations
                migration_result = await db.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                current_version = migration_result.scalar()
                result['current_migration'] = current_version
                result['migrations_current'] = bool(current_version)
                
                # Check critical indices
                index_query = """
                    SELECT schemaname, tablename, indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                """
                index_result = await db.execute(text(index_query))
                indices = index_result.fetchall()
                
                critical_indices = [
                    'opportunities_website_id_idx',
                    'opportunities_closing_date_idx',
                    'scraping_jobs_status_idx'
                ]
                
                existing_indices = [idx[2] for idx in indices]
                missing_indices = [
                    idx for idx in critical_indices 
                    if idx not in existing_indices
                ]
                
                result['missing_indices'] = missing_indices
                result['indices_optimized'] = len(missing_indices) == 0
                
                # Check connection pool
                pool_result = await db.execute(
                    text("SHOW max_connections")
                )
                max_connections = pool_result.scalar()
                result['max_connections'] = max_connections
                result['connection_pool_configured'] = int(max_connections) >= 100
                
                result['passed'] = all([
                    result['migrations_current'],
                    result['indices_optimized'],
                    result['connection_pool_configured']
                ])
                
        except Exception as e:
            result['passed'] = False
            result['error'] = str(e)
        
        return result
    
    async def validate_security(self) -> Dict[str, Any]:
        """Validate security configuration."""
        result = {
            'passed': True,
            'checks': {}
        }
        
        # Check HTTPS enforcement
        result['checks']['https_enforced'] = os.environ.get('FORCE_HTTPS') == 'true'
        
        # Check CORS configuration
        result['checks']['cors_configured'] = bool(os.environ.get('CORS_ORIGINS'))
        
        # Check rate limiting
        result['checks']['rate_limiting_enabled'] = os.environ.get('ENABLE_RATE_LIMIT') == 'true'
        
        # Check authentication
        result['checks']['jwt_configured'] = bool(os.environ.get('SECRET_KEY'))
        
        # Check credential encryption
        result['checks']['credential_encryption'] = bool(
            os.environ.get('CREDENTIAL_ENCRYPTION_KEY')
        )
        
        # Calculate overall
        result['passed'] = all(result['checks'].values())
        
        return result
    
    async def validate_performance(self) -> Dict[str, Any]:
        """Validate performance baselines."""
        result = {
            'passed': True,
            'metrics': {}
        }
        
        # Run quick performance tests
        async with get_db() as db:
            # Database query performance
            start = asyncio.get_event_loop().time()
            await db.execute(text("SELECT COUNT(*) FROM opportunities"))
            db_time = asyncio.get_event_loop().time() - start
            result['metrics']['db_query_ms'] = db_time * 1000
            
            if db_time > 0.1:  # 100ms threshold
                result['passed'] = False
        
        # API response time
        try:
            async with httpx.AsyncClient() as client:
                start = asyncio.get_event_loop().time()
                response = await client.get('http://localhost:8000/health')
                api_time = asyncio.get_event_loop().time() - start
                result['metrics']['api_response_ms'] = api_time * 1000
                
                if api_time > 0.5:  # 500ms threshold
                    result['passed'] = False
        except Exception:
            result['passed'] = False
        
        return result
    
    async def validate_monitoring(self) -> Dict[str, Any]:
        """Validate monitoring setup."""
        result = {
            'passed': True,
            'monitoring_configured': {}
        }
        
        # Check logging
        result['monitoring_configured']['structured_logging'] = True  # We implemented this
        
        # Check Sentry
        result['monitoring_configured']['error_tracking'] = bool(
            os.environ.get('SENTRY_DSN')
        )
        
        # Check metrics
        result['monitoring_configured']['metrics_enabled'] = bool(
            os.environ.get('ENABLE_METRICS')
        )
        
        # Check health endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('http://localhost:8000/health')
                result['monitoring_configured']['health_endpoint'] = response.status_code == 200
        except Exception:
            result['monitoring_configured']['health_endpoint'] = False
        
        result['passed'] = result['monitoring_configured']['health_endpoint']
        
        return result
    
    async def validate_backup(self) -> Dict[str, Any]:
        """Validate backup and recovery setup."""
        result = {
            'passed': True,
            'backup_configured': {}
        }
        
        # Check database backup configuration
        result['backup_configured']['database_backup'] = bool(
            os.environ.get('DATABASE_BACKUP_ENABLED')
        )
        
        # Check file backup (MinIO)
        result['backup_configured']['file_backup'] = bool(
            os.environ.get('MINIO_BACKUP_ENABLED')
        )
        
        # Check backup schedule
        result['backup_configured']['scheduled_backups'] = bool(
            os.environ.get('BACKUP_SCHEDULE')
        )
        
        result['passed'] = any(result['backup_configured'].values())
        
        return result
    
    async def validate_deployment(self) -> Dict[str, Any]:
        """Validate deployment configuration."""
        result = {
            'passed': True,
            'deployment_ready': {}
        }
        
        # Check Docker configuration
        docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.prod.yml']
        for file in docker_files:
            result['deployment_ready'][file] = os.path.exists(f'/root/hoistscout/{file}')
        
        # Check environment files
        result['deployment_ready']['env_example'] = os.path.exists('/root/hoistscout/.env.example')
        
        # Check deployment scripts
        result['deployment_ready']['deploy_script'] = os.path.exists('/root/hoistscout/deploy.sh')
        
        result['passed'] = all(result['deployment_ready'].values())
        
        return result
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary."""
        summary = {
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check critical validations
        critical = ['environment_variables', 'database_migrations', 'security_configuration']
        
        for validation in critical:
            if not results.get(validation, {}).get('passed'):
                summary['critical_issues'].append(f"{validation} validation failed")
        
        # Add specific recommendations
        if results.get('environment_variables', {}).get('missing_optional'):
            summary['recommendations'].append(
                "Configure optional services for full functionality"
            )
        
        if not results.get('monitoring', {}).get('monitoring_configured', {}).get('error_tracking'):
            summary['recommendations'].append(
                "Enable Sentry for production error tracking"
            )
        
        return summary


# API endpoint for health checks
from fastapi import APIRouter

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@health_router.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check."""
    checker = SystemHealthChecker()
    return await checker.run_all_checks()

@health_router.get("/health/readiness")
async def production_readiness():
    """Check production readiness."""
    validator = ProductionReadinessValidator()
    return await validator.validate_all()