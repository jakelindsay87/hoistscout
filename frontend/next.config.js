/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // Optimize build for low memory environments
  swcMinify: true,
  experimental: {
    // Reduce memory usage during build
    workerThreads: false,
    cpus: 1,
  },
  typescript: {
    // Skip TypeScript errors during development
    ignoreBuildErrors: true,
  },
  eslint: {
    // Skip ESLint errors during development
    ignoreDuringBuilds: true,
  },
}

module.exports = nextConfig 