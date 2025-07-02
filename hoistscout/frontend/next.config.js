/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  },
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  },
  // Ensure environment variables are available during build
  webpack: (config, { isServer }) => {
    // Log the API URL during build to help debug
    console.log('Building with NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
    return config;
  }
}

module.exports = nextConfig