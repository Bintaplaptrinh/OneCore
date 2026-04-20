/** @type {import('next').NextConfig} */
const nextConfig = {
  env: { NEXT_PUBLIC_API_URL: '' },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ];
  }
};
export default nextConfig;
