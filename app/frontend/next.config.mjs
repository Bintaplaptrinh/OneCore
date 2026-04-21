/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendBase = (
      process.env.BACKEND_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      'http://localhost:8000'
    ).replace(/\/$/, '');

    return [
      {
        source: '/api/:path*',
        destination: `${backendBase}/api/:path*`
      }
    ];
  }
};
export default nextConfig;
