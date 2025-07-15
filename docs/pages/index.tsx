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
import { JSX } from "react";

export default function Home(): JSX.Element {
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-100 via-white to-purple-300 transition-colors duration-300">
      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-6 lg:px-12 backdrop-blur-sm border-b border-gray-200 bg-white/80">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white/50 rounded-xl border border-gray-300 backdrop-blur-sm">
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
              href: "/",
            },
            {
              label: "Documentation",
              href: "/docs",
            },
            {
              label: "Examples",
              href: "/",
            },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="text-gray-700 hover:text-gray-900 transition-colors font-medium"
            >
              {item.label}
            </Link>
          ))}
        </div>
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-4 text-sm text-gray-700">
            <div className="flex items-center space-x-1">
              <Star className="h-4 w-4 text-yellow-500" />
              <span>5</span>
            </div>
            <div className="flex items-center space-x-1">
              <Users className="h-4 w-4 text-green-500" />
              <span>18</span>
            </div>
          </div>
          <Link
            href="#"
            className="flex items-center space-x-2 px-4 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-100 transition-all duration-300 transform hover:scale-105 !text-gray-900 backdrop-blur-sm"
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
                  Plug into Norma’s infrastructure and the IONOS AI Models Hub
                  to launch a production‑ready RAG chatbot with TF‑IDF indexing,
                  LangChain integration, and scalable best practices baked in.
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
                <button className="inline-flex items-center justify-center space-x-3 px-10 py-5 rounded-xl font-semibold text-xl transition-all duration-300 border border-gray-300 bg-white hover:bg-gray-100 text-gray-900 backdrop-blur-sm">
                  <Github className="h-6 w-6" />
                  <span>View on GitHub</span>
                </button>
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
                src="/assets/hero.png"
                width={500}
                height={500}
                alt="Hero illustration"
                className="w-full !max-w-[600px] rounded-3xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div id="features" className="px-6 py-20 lg:px-12">
        <div className="mx-auto max-w-6xl">
          <div className="grid md:grid-cols-2 gap-10">
            {[
              {
                icon: <Zap className="h-10 w-10 text-green-500" />,
                title: "Index & Retrieve",
                desc: `Rapidly scrape and index any webpage using TF‑IDF and LangChain—delivering lightning‑fast document retrieval out of the box.`,
                tags: ["TF‑IDF", "Web Scraping", "LangChain", "RAG"],
                color: "green",
              },
              {
                icon: <FlaskConical className="h-10 w-10 text-purple-500" />,
                title: "Seamless AI Chat",
                desc: `Engage with your indexed content via the IONOS AI Models Hub, with FastAPI‑powered routing and full conversation history support.`,
                tags: ["FastAPI", "IONOS AI", "Contextual Chat", "History"],
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
                Ready to launch your RAG‑powered chatbot?
              </h2>
              <p className="text-lg sm:text-xl text-gray-600 leading-relaxed">
                Join thousands of developers on Norma’s platform and the IONOS
                AI Models Hub to deploy intelligent, retrieval‑augmented
                chatbots in minutes.
              </p>
              <div className="flex flex-col sm:flex-row justify-center gap-8">
                <Link
                  href="#"
                  className="inline-flex items-center justify-center space-x-2 bg-black hover:bg-gray-900 !text-white px-10 py-4 rounded-xl font-semibold text-base transition-transform hover:scale-105 shadow"
                >
                  <span>View on GitHub</span>
                  <Github className="h-5 w-5" />
                </Link>
                <Link
                  href="#"
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
