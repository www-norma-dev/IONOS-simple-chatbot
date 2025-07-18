import React from "react";
import { DocsThemeConfig } from "nextra-theme-docs";
import Link from "next/link";
const config: DocsThemeConfig = {
  logo: (
    <>
      <span style={{ fontWeight: 800, fontSize: "1.2em" }}>
        IONOS Agent Starter Pack
      </span>
    </>
  ),
  search: { placeholder: "Search docs..." },
  project: { link: "https://github.com/www-norma-dev/IONOS-simple-chatbot" },

  feedback: {
    content: "Have suggestions? Let us know →",
    labels: "feedback",
  },
  editLink: { content: null },
  docsRepositoryBase: "https://github.com/www-norma-dev/IONOS-simple-chatbot",
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta
        name="description"
        content="IONOS Agent Starter Pack Documentation"
      />
      <meta property="og:title" content="IONOS Agent Docs" />
    </>
  ),
  banner: {
    key: "ionos-v1",
    content: (
      <div className="flex items-center justify-center gap-3 text-sm font-medium bg-gradient-to-r from-[#00E6B4] to-[#726DFE] text-white p-4">
        <span>IONOS Agent Docs v1.0 just launched!</span>
        <Link
          href="https://github.com/www-norma-dev/IONOS-simple-chatbot"
          target="_blank"
          rel="noreferrer"
          className="rounded bg-black px-3 py-1 text-white hover:bg-gray-800 transition"
        >
          ⭐ Star us on GitHub
        </Link>
      </div>
    ),
  },
  footer: {
    content: (
      <div className="w-full text-center text-xs text-gray-500 py-8 border-t border-gray-200">
        <span>
          © {new Date().getFullYear()} MIT —{" "}
          <Link
            href="https://github.com/www-norma-dev/IONOS-simple-chatbot"
            target="_blank"
            rel="noreferrer"
            className="underline hover:text-gray-700 transition-colors"
          >
            IONOS Agent Project
          </Link>
        </span>
      </div>
    ),
  },
  navigation: { prev: true, next: true },
  darkMode: true,
  themeSwitch: {
    useOptions() {
      return { light: "Light", dark: "Dark", system: "System" };
    },
  },
  toc: { float: true },
};

export default config;
