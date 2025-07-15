// next.config.js   (or .ts)

import nextra from "nextra";

// 1️⃣ Instantiate Nextra with its options:
const withNextra = nextra({
  theme: "nextra-theme-docs",
  themeConfig: "./theme.config.tsx",
});

// 2️⃣ Wrap your Next.js config by passing it into the function:
export default withNextra({
  pageExtensions: ["js", "jsx", "ts", "tsx", "md", "mdx"],
  reactStrictMode: true,
  output: "export",
  images: {
    unoptimized: true,
  },
  basePath: "/IONOS-simple-chatbot",
  assetPrefix: "/IONOS-simple-chatbot/",
});
