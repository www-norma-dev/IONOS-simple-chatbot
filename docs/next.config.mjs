// next.config.js
import nextra from "nextra";

const isProd = process.env.NODE_ENV === "production";
const base = isProd ? "/IONOS-simple-chatbot" : "";
const prefix = isProd ? "/IONOS-simple-chatbot/" : "";

const withNextra = nextra({
  theme: "nextra-theme-docs",
  themeConfig: "./theme.config.tsx",
});

export default withNextra({
  pageExtensions: ["js", "jsx", "ts", "tsx", "md", "mdx"],
  reactStrictMode: true,

  output: "export",
  images: { unoptimized: true },

  basePath: base,
  assetPrefix: prefix,

  env: {
    NEXT_PUBLIC_BASE_PATH: base,
  },
});
