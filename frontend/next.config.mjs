/** @type {import('next').NextConfig} */
const rawBackendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const backendOrigin = rawBackendUrl
	.replace(/\/api\/v1\/?$/, "")
	.replace(/\/$/, "")
	.replace("http://localhost:", "http://127.0.0.1:")
	.replace("https://localhost:", "https://127.0.0.1:");

const nextConfig = {
	experimental: {
		optimizePackageImports: [
			"recharts",
			"framer-motion",
			"lucide-react",
			"@radix-ui/react-icons",
			"@radix-ui/react-dialog",
			"@radix-ui/react-dropdown-menu",
			"@radix-ui/react-popover",
			"@radix-ui/react-select",
			"@radix-ui/react-tabs",
			"@radix-ui/react-tooltip",
			"@radix-ui/react-accordion",
			"@radix-ui/react-avatar",
			"@radix-ui/react-checkbox",
			"@radix-ui/react-label",
			"date-fns",
			"lodash",
			"zod",
		],
	},

	compress: true,
	swcMinify: true,
	reactStrictMode: false,

	compiler: {
		removeConsole:
			process.env.NODE_ENV === "production"
				? { exclude: ["error", "warn"] }
				: false,
	},

	images: {
		formats: ["image/avif", "image/webp"],
		minimumCacheTTL: 86400,
	},

	async rewrites() {
		return [
			{
				source: "/api/:path*",
				destination: `${backendOrigin}/api/:path*`,
			},
		];
	},

	async headers() {
		return [
			{
				source: "/_next/static/:path*",
				headers: [
					{
						key: "Cache-Control",
						value: "public, max-age=31536000, immutable",
					},
				],
			},
		];
	},

	webpack(config, { isServer, dev }) {
		if (dev) {
			// OneDrive/Windows file-locking can corrupt webpack cache packs and break HMR chunk factories.
			config.cache = false;
		}
		return config;
	},
};

export default nextConfig;
