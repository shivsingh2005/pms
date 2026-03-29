/** @type {import('next').NextConfig} */
const rawBackendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const backendOrigin = rawBackendUrl
	.replace(/\/api\/v1\/?$/, "")
	.replace(/\/$/, "")
	.replace("http://localhost:", "http://127.0.0.1:")
	.replace("https://localhost:", "https://127.0.0.1:");

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
