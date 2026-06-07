/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Clean redirect mapping / to /dashboard
  async redirects() {
    return [
      {
        source: '/',
        destination: '/dashboard',
        permanent: true,
      },
    ]
  },
  
  // Custom CORS, Content Security, and developmental resource headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET,POST,OPTIONS,PUT,DELETE',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Origin, X-Requested-With, Content-Type, Accept, Authorization',
          },
        ],
      },
    ]
  },
};

module.exports = nextConfig;
