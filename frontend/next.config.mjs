/** @type {import('next').NextConfig} */
const rawBackendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const backendOrigin = rawBackendUrl.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");

const nextConfig = {
	async rewrites() {
		return [
			{
				source: "/api/:path*",
				destination: `${backendOrigin}/api/:path*`,
			},
		];
	},
};

export default nextConfig;
