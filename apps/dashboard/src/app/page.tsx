"use client";

import React from "react";
import Link from "next/link";
import { motion, type Variants } from "framer-motion";
import { 
  Zap, 
  ArrowRight, 
  Play, 
  Layers, 
  ShieldCheck, 
  Globe,
  Database,
  Users,
  ShieldAlert
} from "lucide-react";
import { cn } from "@/lib/utils";

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
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-brand-dark text-white selection:bg-cyan-glow selection:text-black font-sans">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-brand-dark/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-linear-to-br from-violet-600 to-cyan-500 flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)]">
              <Zap className="h-6 w-6 text-white fill-white" />
            </div>
            <span className="text-2xl font-black tracking-tighter uppercase">AlphaHecta</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <NavLink href="#products">Products</NavLink>
            <NavLink href="#marketplace">Marketplace</NavLink>
            <NavLink href="#solutions">Solutions</NavLink>
            <NavLink href="#pricing">Pricing</NavLink>
            <NavLink href="#about">About</NavLink>
          </div>

          <Link href="/login" className="bg-cyan-glow hover:bg-cyan-glow/90 text-black font-black px-6 py-2.5 rounded-xl transition-all text-sm uppercase tracking-widest">
            Get Started
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
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-glow/10 border border-cyan-glow/20">
              <div className="h-1.5 w-1.5 rounded-full bg-cyan-glow animate-pulse" />
              <span className="text-[10px] font-black uppercase tracking-widest text-cyan-glow">Next Gen Autonomous AI Orchestration</span>
            </motion.div>
            
            <motion.h1 variants={itemVariants} className="text-6xl md:text-7xl font-black tracking-tighter leading-[0.9] uppercase">
              Deploy Production-Ready AI <br />
              <span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-glow via-emerald-accent to-violet-500">In Days, Not Months</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="text-zinc-500 text-lg font-medium max-w-xl leading-relaxed">
              The unified platform to deploy autonomous agents, enforce regulatory compliance, and protect your brand from synthetic threats with military grade precision.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-wrap gap-4 pt-4">
              <Link href="/register" className="bg-violet-600 hover:bg-violet-700 text-white font-black px-8 py-4 rounded-2xl transition-all flex items-center gap-3 group shadow-lg shadow-violet-600/20">
                Start Building <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <button className="bg-white/5 hover:bg-white/10 border border-white/10 text-white font-black px-8 py-4 rounded-2xl transition-all flex items-center gap-3">
                <Play className="h-5 w-5 fill-white" /> View Demo
              </button>
            </motion.div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9, x: 20 }}
            whileInView={{ opacity: 1, scale: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="relative"
          >
            <div className="absolute -inset-4 bg-linear-to-r from-cyan-glow/20 via-violet-500/10 to-emerald-accent/20 blur-3xl opacity-30 animate-pulse" />
            <div className="glass-card p-2 rounded-[2.5rem] border-white/10 relative overflow-hidden group">
              <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
              <div className="bg-zinc-950 rounded-[2rem] aspect-video flex items-center justify-center border border-white/5 overflow-hidden">
                {/* Mockup Dashboard Preview */}
                <div className="w-full h-full p-6 space-y-6 opacity-40 group-hover:opacity-100 transition-opacity duration-700">
                  <div className="h-8 w-1/3 bg-white/5 rounded-lg" />
                  <div className="grid grid-cols-3 gap-4 h-32">
                    <div className="bg-white/5 rounded-xl border border-white/5" />
                    <div className="bg-white/5 rounded-xl border border-white/5" />
                    <div className="bg-white/5 rounded-xl border border-white/5" />
                  </div>
                  <div className="h-40 w-full bg-white/5 rounded-2xl border border-white/5" />
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                   <div className="h-16 w-16 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 flex items-center justify-center group-hover:scale-110 transition-transform cursor-pointer">
                     <Play className="h-8 w-8 text-white fill-white ml-1" />
                   </div>
                </div>
              </div>
            </div>
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
            <MetricTile label="Uptime" value="99.99%" />
            <MetricTile label="Global Clients" value="10K+" />
            <MetricTile label="Venture Funding" value="$100M+" />
            <MetricTile label="Daily Predictions" value="1B+" />
          </motion.div>
        </section>

        {/* 3 Simple Steps */}
        <section className="max-w-7xl mx-auto mb-32 text-center space-y-16">
          <div className="space-y-4">
            <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tighter">Production AI in 3 Simple Steps</h2>
            <p className="text-zinc-500 font-medium max-w-xl mx-auto uppercase text-xs tracking-widest">We've abstracted the complexity of enterprise AI infrastructure.</p>
          </div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <StepCard 
              icon={<Database className="h-8 w-8 text-cyan-glow" />} 
              title="Connect Your Stack" 
              description="Securely integrate enterprise data, cloud infrastructure, and existing software beds." 
            />
            <StepCard 
              icon={<Users className="h-8 w-8 text-violet-500" />} 
              title="Deploy Agents" 
              description="Launch specialized AI workflows tailored to your agents' workflows and business logic." 
            />
            <StepCard 
              icon={<ShieldCheck className="h-8 w-8 text-emerald-accent" />} 
              title="Scale & Protect" 
              description="Maintain performance in production while enforcing system-level compliance and safety." 
            />
          </motion.div>
        </section>

        {/* The Portfolio */}
        <section className="max-w-7xl mx-auto mb-32 space-y-16">
          <div className="text-center">
            <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tighter underline decoration-cyan-glow decoration-8 underline-offset-8">The Portfolio</h2>
          </div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <PortfolioCard 
              icon={<Layers className="h-10 w-10 text-cyan-glow" />} 
              title="AgentOps" 
              description="Autonomous companies and solution-led platforms built to orchestrate the future of enterprise." 
              tag="FEATURED"
            />
            <PortfolioCard 
              icon={<Globe className="h-10 w-10 text-emerald-accent" />} 
              title="AI Compliance Hub" 
              description="AI Governance frameworks dedicated to ensuring ethical and regulatory AI operationalization." 
              tag="ENTERPRISE"
            />
            <PortfolioCard 
              icon={<ShieldAlert className="h-10 w-10 text-violet-500" />} 
              title="Deepfake Defense" 
              description="Real-time detection and mitigation of synthetic media across enterprise communication channels." 
              tag="SECURITY"
            />
          </motion.div>
        </section>
      </main>

      {/* Footer Footer */}
      <footer className="border-t border-white/5 py-12 bg-zinc-950/50">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-3 opacity-50">
            <Zap className="h-5 w-5" />
            <span className="font-black uppercase tracking-widest text-sm">AlphaHecta</span>
          </div>
          <div className="text-zinc-600 text-[10px] font-black uppercase tracking-widest">
            © 2026 ALPHAHECTA TECHNOLOGIES. ALL RIGHTS RESERVED.
          </div>
        </div>
      </footer>
    </div>
  );
}

function NavLink({ href, children }: { href: string, children: React.ReactNode }) {
  return (
    <Link href={href} className="text-zinc-500 hover:text-white font-bold text-sm uppercase tracking-widest transition-colors">
      {children}
    </Link>
  );
}

function MetricTile({ label, value }: { label: string, value: string }) {
  return (
    <motion.div variants={itemVariants} className="glass-card p-8 rounded-4xl border-white/5 hover:border-cyan-glow/30 transition-all group overflow-hidden relative">
      <div className="absolute inset-0 bg-linear-to-br from-cyan-glow/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <p className="text-4xl font-black tracking-tighter mb-2">{value}</p>
      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600 group-hover:text-cyan-glow transition-colors">{label}</p>
    </motion.div>
  );
}

function StepCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div variants={itemVariants} className="glass-card p-10 rounded-[3rem] border-white/5 hover:border-violet-500/30 transition-all text-left space-y-6 group">
      <div className="h-16 w-16 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <div className="space-y-4">
        <h3 className="text-2xl font-black uppercase tracking-tighter">{title}</h3>
        <p className="text-zinc-500 text-sm font-medium leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

function PortfolioCard({ icon, title, description, tag }: { icon: React.ReactNode, title: string, description: string, tag: string }) {
  return (
    <motion.div variants={itemVariants} className="glass-card p-10 rounded-[3rem] border-white/5 hover:border-emerald-accent/30 transition-all text-left space-y-8 group relative overflow-hidden">
       <div className="absolute top-6 right-6">
         <span className="text-[9px] font-black px-3 py-1 bg-white/5 border border-white/10 rounded-full text-zinc-500 tracking-widest uppercase">{tag}</span>
       </div>
       <div className="h-20 w-20 rounded-[2rem] bg-white/3 border border-white/5 flex items-center justify-center group-hover:rotate-6 transition-all duration-500">
        {icon}
      </div>
      <div className="space-y-4">
        <h3 className="text-3xl font-black uppercase tracking-tighter">{title}</h3>
        <p className="text-zinc-500 font-medium leading-relaxed">{description}</p>
      </div>
      <button className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.2em] text-emerald-accent group-hover:gap-4 transition-all">
        Explore Project <ArrowRight className="h-4 w-4" />
      </button>
    </motion.div>
  );
}
