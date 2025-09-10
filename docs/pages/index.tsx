import {
  Github,
  ArrowRight,
  Zap,
  FlaskConical,
  Bot,
  Star,
  Users,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import type { GetStaticProps } from "next";
import { JSX } from "react";
import { PlayCircle, PauseCircle } from "lucide-react";
import { useRef, useState } from "react";

type Props = {
  stars: number | null;
  contributors: number | null;
};

export const getStaticProps: GetStaticProps<Props> = async () => {
  const repoApi =
    "https://api.github.com/repos/www-norma-dev/IONOS-simple-chatbot";
  const contributorsApi =
    "https://api.github.com/repos/www-norma-dev/IONOS-simple-chatbot/contributors?per_page=100&anon=1";

  let stars: number | null = null;
  let contributors: number | null = null;

  try {
    const [repoRes, contribRes] = await Promise.all([
      fetch(repoApi, { headers: { Accept: "application/vnd.github+json" } }),
      fetch(contributorsApi, {
        headers: { Accept: "application/vnd.github+json" },
      }),
    ]);

    if (repoRes.ok) {
      const repoJson = await repoRes.json();
      // stargazers_count is the star count
      if (typeof repoJson?.stargazers_count === "number") {
        stars = repoJson.stargazers_count;
      }
    }

    if (contribRes.ok) {
      const contribJson = (await contribRes.json()) as Array<unknown>;
      if (Array.isArray(contribJson)) {
        contributors = contribJson.length;
      }
    }
  } catch {
    // Fail silently and keep nulls so build doesn't fail
  }

  return {
    props: { stars, contributors },
  };
};

export default function Home({ stars, contributors }: Props): JSX.Element {
  const base = process.env.NEXT_PUBLIC_BASE_PATH || "";

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const videoSrc = `${base}/assets/video-chatbot.mp4`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-100 via-white to-purple-300 transition-colors duration-300">
      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-6 lg:px-12 backdrop-blur-sm border-b border-gray-200 bg-white/80">
        <div className="flex items-center space-x-3">
          <div className="p-5 bg-white/50 rounded-xl border border-gray-300 backdrop-blur-sm">
            <Bot className="h-6 w-6 text-blue-600" />
          </div>
          <span className="text-xl font-bold text-gray-900">
            IONOS Agent Starter Pack
          </span>
        </div>
        <div className="hidden md:flex items-center space-x-8">
          {[
            {
              label: "Features",
              scrollToId: "features",
            },
            {
              label: "Documentation",
              href: "/docs",
            },
          ].map((item) => (
            <div key={item.label}>
              {item.href ? (
                <Link
                  key={item.label}
                  href={item.href}
                  className="text-gray-700 hover:text-gray-900 transition-colors"
                >
                  <span className="font-medium">{item.label}</span>
                </Link>
              ) : (
                <button
                  key={item.label}
                  onClick={() => {
                    const section = document.getElementById(item.scrollToId!);
                    if (section) section.scrollIntoView({ behavior: "smooth" });
                  }}
                  className="text-gray-700 hover:text-gray-900 transition-colors bg-transparent border-none p-0 cursor-pointer"
                >
                  <span className="font-medium">{item.label}</span>
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-4 text-sm text-gray-700">
            <div className="flex items-center space-x-1">
              <Star className="h-4 w-4 text-yellow-500" />
              <span aria-label="GitHub stars">{stars ?? "—"}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Users className="h-4 w-4 text-green-500" />
              <span aria-label="Contributors">{contributors ?? "—"}</span>
            </div>
          </div>
          <Link
            href="https://github.com/www-norma-dev/IONOS-simple-chatbot"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 px-4 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 text-gray-900 backdrop-blur-sm"
          >
            <Github className="h-4 w-4" />
            <span className="hidden sm:inline">GitHub</span>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative px-6 py-16 lg:px-12 lg:py-24">
        <div className="mx-auto max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Left Content */}
            <div className="space-y-10">
              {/* Badge */}
              <div className="inline-flex items-center space-x-2 rounded-full bg-white/80 border border-gray-200 px-4 py-2 text-sm text-blue-600 backdrop-blur-sm">
                <Zap className="h-4 w-4" />
                <span>Production-Ready AI Agents</span>
              </div>

              {/* Main Heading */}
              <div className="space-y-6">
                <h1 className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold text-gray-900 leading-tight">
                  Build AI Agents{" "}
                  <span className="block bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500">
                    That Actually Work
                  </span>
                </h1>
                <p className="text-xl lg:text-2xl text-gray-700 leading-relaxed font-medium  max-w-2xl">
                  Plug into the IONOS AI Models Hub and Norma’s AI evaluation to
                  launch a production‑ready Agents, LangChain integration, and
                  scalable best practices baked in.
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-6">
                <Link
                  href="/docs"
                  className="group inline-flex items-center justify-center space-x-3  bg-[#726DFE] !text-white px-10 py-5 rounded-xl font-semibold text-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
                >
                  <span>Get Started Guide</span>
                  <ArrowRight className="h-6 w-6 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  href="https://github.com/www-norma-dev/IONOS-simple-chatbot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center space-x-3 px-10 py-5 rounded-xl font-semibold text-xl transition-all duration-300 border border-gray-300 bg-white hover:bg-gray-100 text-gray-900 backdrop-blur-sm"
                >
                  <Github className="h-6 w-6" />
                  <span>View on GitHub</span>
                </Link>
              </div>

              {/* Stats */}
              <div className="flex space-x-12 pt-6">
                {[
                  { value: "4+", label: "Agent Templates", color: "blue-600" },
                  { value: "100%", label: "Open Source", color: "green-600" },
                  {
                    value: "⚡",
                    label: "Production Ready",
                    color: "purple-600",
                  },
                ].map((stat) => (
                  <div key={stat.label} className="text-center">
                    <div className={`text-3xl font-bold text-${stat.color}`}>
                      {stat.value}
                    </div>
                    <div className="text-sm text-gray-700">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Image */}
            <div className="relative lg:order-last">
              <Image
                src={`${base}/assets/hero.png`}
                width={500}
                height={500}
                alt="Hero illustration"
                unoptimized
                className="w-full !max-w-[600px] rounded-3xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Video Section (under Hero) */}
      <section className="px-6 pb-20 lg:px-12">
        <div className="mx-auto max-w-5xl text-center">
          {/* Glassmorphism video frame with subtle glow */}
          <div className="relative group">
            {/* gradient border wrapper */}
            <div className="p-[20px] rounded-3xl bg-gradient-to-r from-teal-400/30 via-purple-500/30 to-purple-400/30">
              <div className="relative rounded-3xl overflow-hidden border border-white/40 bg-white/30 backdrop-blur-xl shadow-2xl">
                {/* the video */}
                <video
                  ref={videoRef}
                  src={videoSrc}
                  className="w-full aspect-video"
                  preload="metadata"
                  controls={playing}
                  playsInline
                  onPlay={() => setPlaying(true)}
                  onPause={() => setPlaying(false)}
                  onEnded={() => setPlaying(false)}
                />

                {/* Play overlay */}
                {!playing && (
                  <button
                    aria-label="Play video"
                    onClick={() => {
                      const v = videoRef.current;
                      if (v) v.play();
                    }}
                    className="absolute inset-0 flex items-center justify-center"
                  >
                    {/* animated ring */}
                    <span className="absolute h-24 w-24 rounded-full ring-8 ring-white/40 animate-ping" />
                    {/* glass play button */}
                    <span
                      className="relative inline-flex items-center justify-center h-20 w-20 rounded-full
                               bg-white/40 border border-white/60 backdrop-blur-xl shadow-xl
                               transition-transform duration-200 group-hover:scale-105"
                    >
                      <PlayCircle className="h-12 w-12 text-purple-500" />
                    </span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <div id="features" className="px-6 py-20 lg:px-12">
        <div className="mx-auto max-w-6xl">
          <div className="grid md:grid-cols-2 gap-10">
            {[
              {
                icon: <Zap className="h-10 w-10 text-green-500" />,
                title: "Adaptive Knowledge Search",
                desc: `Search and retrieve fresh information from the open web in real time, powered by ReAct-style reasoning. The chatbot continuously adapts its knowledge without being tied to pre-scraped datasets.`,
                tags: [
                  "Web Search",
                  "ReAct",
                  "Dynamic Context",
                  "Real-time Retrieval",
                ],
                color: "green",
              },
              {
                icon: <FlaskConical className="h-10 w-10 text-purple-500" />,
                title: "Context-Aware Conversations",
                desc: `Interact with an AI that remembers, reasons, and adapts. Powered by the IONOS AI Models Hub and ReAct Agents, conversations flow naturally with contextual awareness across multiple turns.`,
                tags: [
                  "ReAct Agent",
                  "IONOS AI",
                  "Multi-turn Context",
                  "Reasoning",
                ],
                color: "purple",
              },
            ].map(({ icon, title, desc, tags, color }) => (
              <div
                key={title}
                className="group relative bg-white border border-gray-200 rounded-2xl p-10 hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]"
              >
                <div className="flex items-center space-x-4 mb-8">
                  <div
                    className={`p-4 bg-${color}-100 rounded-2xl border border-${color}-200`}
                  >
                    {icon}
                  </div>
                  <h3 className="text-3xl font-bold text-gray-900">{title}</h3>
                </div>
                <p className="text-lg text-gray-700 leading-relaxed mb-10">
                  {desc}
                </p>
                <div className="flex flex-wrap gap-3">
                  {tags.map((t) => (
                    <span
                      key={t}
                      className={`px-4 py-2 bg-${color}-100 text-${color}-600 rounded-full text-sm font-medium border border-${color}-200`}
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="py-32 px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <div className="relative overflow-hidden rounded-3xl bg-white p-16 shadow-2xl">
            {/* subtle gradient glow behind the card */}
            <div className="relative !space-y-5">
              <h2 className="text-5xl sm:text-6xl font-extrabold text-gray-900 leading-tight">
                Ready to launch your intelligent assistant?
              </h2>
              <p className="text-lg sm:text-xl text-gray-600 leading-relaxed">
                With the IONOS Starter Pack, deploy context-aware, web-connected
                chatbots in minutes. Thousands of developers already use Norma’s
                platform and the IONOS AI Models Hub to create next-generation
                AI agents.
              </p>
              <div className="flex flex-col sm:flex-row justify-center gap-8">
                <Link
                  href="https://github.com/www-norma-dev/IONOS-simple-chatbot"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center space-x-2 bg-black hover:bg-gray-900 !text-white px-10 py-4 rounded-xl font-semibold text-base transition-transform hover:scale-105 shadow"
                >
                  <span>View on GitHub</span>
                  <Github className="h-5 w-5" />
                </Link>
                <Link
                  href="/docs"
                  className="inline-flex items-center justify-center space-x-2 bg-white hover:bg-gray-100 text-blue-600 px-10 py-4 rounded-xl font-semibold text-base transition-transform hover:scale-105 border border-blue-200 shadow"
                >
                  <span>Read Documentation</span>
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
