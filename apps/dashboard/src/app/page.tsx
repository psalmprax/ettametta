"use client";

import React from "react";
import Link from "next/link";
import { motion, type Variants } from "framer-motion";
import { 
  Zap, 
  ArrowRight, 
  Play, 
  Sparkles,
  TrendingUp,
  Search,
  Crown
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { BaseLayout } from "@/components/layout/BaseLayout";

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.3
    }
  }
};

const itemVariants: Variants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] }
  }
}

function NavLink({ href, children }: { readonly href: string, readonly children: React.ReactNode }) {
  return (
    <Link href={href} className="text-slate-600 hover:text-slate-900 font-medium transition-colors">
      {children}
    </Link>
  );
}

function MetricTile({ label, value }: { readonly label: string, readonly value: string }) {
  return (
    <motion.div variants={itemVariants} className="surface-elevated rounded-2xl hover:shadow-lg transition-all p-8 text-center group">
      <p className="text-4xl font-bold tracking-tight mb-2 text-slate-900 group-hover:text-indigo-600 transition-colors">{value}</p>
      <p className="text-sm font-medium text-slate-500">{label}</p>
    </motion.div>
  );
}

function StepCard({ icon, title, description }: { readonly icon: React.ReactNode, readonly title: string, readonly description: string }) {
  return (
    <motion.div variants={itemVariants} className="surface-card rounded-2xl border hover:shadow-lg transition-all text-left space-y-6 p-8 group">
      <div className="h-14 w-14 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <div className="space-y-3">
        <h3 className="text-xl font-bold tracking-tight text-slate-900">{title}</h3>
        <p className="text-slate-600 leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

function PortfolioCard({ icon, title, description, tag, href }: { readonly icon: React.ReactNode, readonly title: string, readonly description: string, readonly tag: string, readonly href: string }) {
  return (
    <motion.div variants={itemVariants} className="surface-card rounded-2xl border hover:shadow-lg transition-all text-left space-y-6 p-8 group relative overflow-hidden">
      <div className="absolute top-5 right-5">
        <span className="text-[10px] font-bold px-3 py-1.5 bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-full tracking-wide uppercase">{tag}</span>
      </div>
      <div className="h-16 w-16 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <div className="space-y-4">
        <h3 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h3>
        <p className="text-slate-600 leading-relaxed">{description}</p>
      </div>
      <Link href={href}>
        <button className="flex items-center gap-2 text-xs font-semibold text-indigo-600 group-hover:gap-4 transition-all">
          Explore Platform <ArrowRight className="h-4 w-4" />
        </button>
      </Link>
    </motion.div>
  );
}

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading || user) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <BaseLayout variant="landing" withBackground withPattern>
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-linear-to-br from-indigo-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-200">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">Ettametta<span className="text-indigo-600">OS</span></span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <NavLink href="#products">Platform</NavLink>
            <NavLink href="#marketplace">Solutions</NavLink>
            <NavLink href="#solutions">Resources</NavLink>
          </div>

          <Link href="/login">
            <Button variant="primary" size="md">
              Get Started <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center mb-32">
          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={containerVariants}
            className="space-y-8"
          >
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100">
              <div className="h-2 w-2 rounded-full bg-indigo-600 animate-pulse" />
              <span className="text-xs font-semibold text-indigo-700">Intelligence Platform v4.0.2</span>
            </motion.div>
            
            <motion.h1 variants={itemVariants} className="text-4xl md:text-5xl lg:text-7xl font-bold tracking-tight leading-[0.95] text-slate-900">
              Autonomous Intelligence <br />
              <span className="text-indigo-600">For Modern Content</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="text-slate-600 text-lg md:text-xl font-medium max-w-xl leading-relaxed">
              Find trends before they peak, transform them with AI synthesis, and dominate the global feed. The ultimate intelligence suite for creators.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-wrap gap-4 pt-4">
              <Link href="/register">
                <Button variant="primary" size="lg" rounded="full">
                  Begin Setup <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              </Link>
              <Button 
                variant="outline" 
                size="lg" 
                rounded="full"
                onClick={() => scrollToSection("how-it-works")}
              >
                <Play className="h-5 w-5 fill-indigo-600 mr-2" />
                Watch Demo
              </Button>
            </motion.div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            whileInView={{ opacity: 1, scale: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="relative"
          >
            <div className="absolute -inset-4 bg-linear-to-br from-indigo-400/20 via-indigo-500/5 to-amber-400/10 blur-3xl" />
            <Card variant="elevated" className="p-3 rounded-3xl relative overflow-hidden">
              <div className="bg-slate-50 rounded-2xl aspect-video flex items-center justify-center overflow-hidden relative">
                <img 
                    src="/globe.svg" 
                    alt="Content Dashboard" 
                    className="w-full h-full object-cover opacity-90 hover:scale-105 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-linear-to-t from-slate-900/60 via-transparent to-transparent" />
                <div className="absolute bottom-6 left-6 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-emerald-400 rounded-full animate-ping" />
                    <span className="font-mono text-[10px] text-white/90 tracking-widest">LIVE FEED</span>
                  </div>
                  <p className="text-xl font-bold text-white tracking-tight">Global Content Stream</p>
                </div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div 
                  className="h-14 w-14 rounded-full bg-white/90 backdrop-blur-sm border border-white/40 flex items-center justify-center shadow-lg hover:scale-105 transition-all cursor-pointer"
                  onClick={() => scrollToSection("how-it-works")}
                >
                  <Play className="h-7 w-7 text-indigo-600 ml-0.5" />
                </div>
              </div>
            </Card>
          </motion.div>
        </section>

        {/* Metrics Section */}
        <section className="max-w-7xl mx-auto mb-32">
          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            <MetricTile label="Active Users" value="50K+" />
            <MetricTile label="Content Generated" value="2M+" />
            <MetricTile label="Avg. Engagement" value="4.8x" />
            <MetricTile label="Platforms" value="12+" />
          </motion.div>
        </section>

        {/* 3 Simple Steps */}
        <section id="how-it-works" className="max-w-7xl mx-auto mb-32 text-center space-y-16">
          <div className="space-y-4">
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900">How It Works</h2>
            <p className="text-slate-500 font-medium max-w-xl mx-auto">From discovery to publishing — fully automated in three simple steps.</p>
          </div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <StepCard 
              icon={<Search className="h-8 w-8 text-indigo-600" />} 
              title="Discover Trends" 
              description="AI identifies high-velocity viral candidates across global data streams." 
            />
            <StepCard 
              icon={<Sparkles className="h-8 w-8 text-indigo-500" />} 
              title="Create Content" 
              description="Transform and synthesize with AI-driven enhancement tools." 
            />
            <StepCard 
              icon={<Crown className="h-8 w-8 text-indigo-700" />} 
              title="Publish & Scale" 
              description="Automate multi-platform publishing and optimize for growth." 
            />
          </motion.div>
        </section>

        {/* The Platform */}
        <section id="products" className="max-w-7xl mx-auto mb-32 space-y-16">
          <div className="text-center">
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900">
              <span className="text-indigo-600 border-b-2 border-indigo-200 pb-2">The Platform</span>
            </h2>
          </div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <PortfolioCard 
              icon={<Search className="h-10 w-10 text-indigo-600" />} 
              title="Trend Discovery" 
              description="Real-time trend scanning and predictive scoring across global platforms." 
              tag="DISCOVER"
              href="/discovery"
            />
            <PortfolioCard 
              icon={<Sparkles className="h-10 w-10 text-indigo-500" />} 
              title="AI Studio" 
              description="Intelligent content transformation with advanced synthesis tools." 
              tag="CREATE"
              href="/creation"
            />
            <PortfolioCard 
              icon={<TrendingUp className="h-10 w-10 text-indigo-600" />} 
              title="Growth Engine" 
              description="Multi-platform publishing and revenue optimization suite." 
              tag="GROW"
              href="/publishing"
            />
          </motion.div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-12 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8 text-sm font-medium text-slate-500">
          <div className="flex items-center gap-3">
            <Zap className="h-5 w-5 text-indigo-600" />
            <span>Ettametta<span className="text-indigo-600">OS</span></span>
          </div>
          <div className="text-slate-400">
            © 2026 Ettametta Systems. All rights reserved.
          </div>
        </div>
      </footer>
    </BaseLayout>
  );
}
