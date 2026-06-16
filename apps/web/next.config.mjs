/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  images: {
    unoptimized: true
  },
  reactStrictMode: true
};

export default nextConfig;
