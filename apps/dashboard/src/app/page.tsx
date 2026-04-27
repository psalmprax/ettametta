import React from "react";
import Link from "next/link";
import { motion, type Variants } from "framer-motion";
import { 
  Zap, 
  ArrowRight, 
  Play, 
  Layers, 
  Search, 
  Globe,
  Sparkles,
  Crown,
  TrendingUp
} from "lucide-react";
import { cn } from "@/lib/utils";
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
};

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading || user) {
    return (
      <div className="min-h-screen bg-bg-base flex items-center justify-center">
        <div className="h-12 w-12 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <BaseLayout variant="landing" withBackground withPattern>
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-bg-base/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-cyan-500 flex items-center justify-center shadow-[0_0_20px_rgba(0,251,251,0.3)]">
              <Zap className="h-6 w-6 text-black fill-black" />
            </div>
            <span className="text-2xl font-bold tracking-tight uppercase text-white">Ettametta<span className="text-cyan-400">OS</span></span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-[11px] font-bold tracking-[0.2em] text-zinc-500 uppercase">
            <NavLink href="#products">SYSTEM_CORE</NavLink>
            <NavLink href="#marketplace">NEXUS_SYNC</NavLink>
            <NavLink href="#solutions">PROTOCOLS</NavLink>
          </div>

          <Link href="/login">
            <Button variant="primary" size="md">
              INITIALIZE_ACCESS
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
            <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-400/10 border border-cyan-400/20">
              <div className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-400">SYSTEM_STABLE // V4.0.2</span>
            </motion.div>
            
            <motion.h1 variants={itemVariants} className="text-4xl md:text-5xl lg:text-7xl font-bold tracking-tight leading-[0.9] uppercase text-white">
              Autonomous Intelligence <br />
              <span className="text-cyan-400">For Modern Content</span>
            </motion.h1>

            <motion.p variants={itemVariants} className="text-zinc-400 text-lg md:text-xl font-medium max-w-xl leading-relaxed">
              Find trends before they peak, transform them with high-end AI synthesis, and dominate the global feed. The ultimate intelligence suite for creators.
            </motion.p>

            <motion.div variants={itemVariants} className="flex flex-wrap gap-4 pt-4">
              <Link href="/register">
                <Button variant="primary" size="lg" className="rounded-full">
                  Begin Initialization <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              </Link>
              <Button variant="secondary" size="lg" className="rounded-full">
                <Play className="h-5 w-5 fill-white mr-2" /> View Protocols
              </Button>
            </motion.div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9, x: 20 }}
            whileInView={{ opacity: 1, scale: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="relative"
          >
            <div className="absolute -inset-4 bg-gradient-to-r from-cyan-400/20 via-cyan-500/10 to-blue-500/20 blur-3xl opacity-30 animate-pulse" />
            <Card variant="glass" className="p-2 rounded-[2.5rem] border-white/10 relative overflow-hidden group">
              <div className="absolute inset-0 scanline opacity-5 pointer-events-none" />
              <div className="bg-bg-base rounded-4xl aspect-video flex items-center justify-center border border-white/5 overflow-hidden relative">
                <img 
                    src="/_next/image?url=%2Fhome%2Fpsalmprax%2F.gemini%2Fantigravity%2Fbrain%2F0062f090-f109-43f9-bcae-caf9a3b45531%2Fviral_content_gallery_mockup_1777245002910.png&w=1080&q=75" 
                    alt="Viral Content Gallery" 
                    className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-1000"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60" />
                <div className="absolute bottom-10 left-10 space-y-2">
                    <div className="flex items-center gap-2">
                        <div className="h-2 w-2 bg-cyan-400 rounded-full animate-ping" />
                        <span className="font-data-mono text-[10px] text-white tracking-widest">LIVE_TREND_STREAM</span>
                    </div>
                    <p className="text-2xl font-bold text-white uppercase tracking-tight">Global Viral Feed</p>
                </div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                   <div className="h-16 w-16 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 flex items-center justify-center group-hover:scale-110 transition-transform cursor-pointer">
                     <Play className="h-8 w-8 text-white fill-white ml-1" />
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
            <MetricTile label="Neural Nodes Scanned" value="1M+" />
            <MetricTile label="Synthesis Speed" value="<60s" />
            <MetricTile label="Protocol Accuracy" value="85%" />
            <MetricTile label="Cluster Support" value="7+" />
          </motion.div>
        </section>

        {/* 3 Simple Steps */}
        <section className="max-w-7xl mx-auto mb-32 text-center space-y-16">
          <div className="space-y-4">
            <h2 className="text-4xl md:text-5xl font-bold uppercase tracking-tight">System Domination Protocols</h2>
            <p className="text-zinc-500 font-bold max-w-xl mx-auto uppercase text-[10px] tracking-[0.3em]">Neural discovery to autonomous publishing — fully automated.</p>
          </div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <StepCard 
              icon={<Search className="h-8 w-8 text-cyan-400" />} 
              title="Neural Discovery" 
              description="AI clusters identify high-velocity viral candidates across global data streams." 
            />
            <StepCard 
              icon={<Sparkles className="h-8 w-8 text-cyan-500" />} 
              title="AI Transformation" 
              description="Synthesize original content with AI-driven voice and face transformation." 
            />
            <StepCard 
              icon={<Crown className="h-8 w-8 text-cyan-600" />} 
              title="Autonomous Growth" 
              description="Scale your digital presence across multiple protocols simultaneously." 
            />
          </motion.div>
        </section>

        {/* The Portfolio */}
        <section className="max-w-7xl mx-auto mb-32 space-y-16">
          <div className="text-center">
            <h2 className="text-4xl md:text-5xl font-bold uppercase tracking-tight underline decoration-cyan-400 decoration-4 underline-offset-8">THE PLATFORM</h2>
          </div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <PortfolioCard 
              icon={<Search className="h-10 w-10 text-cyan-400" />} 
              title="Viral Intelligence" 
              description="Real-time trend scanning and predictive viral scoring across global social clusters." 
              tag="DISCOVERY"
            />
            <PortfolioCard 
              icon={<Sparkles className="h-10 w-10 text-cyan-500" />} 
              title="Synthesis Studio" 
              description="AI-driven content transformation engine with voice cloning and face synthesis." 
              tag="CREATION"
            />
            <PortfolioCard 
              icon={<TrendingUp className="h-10 w-10 text-cyan-600" />} 
              title="Empire Expansion" 
              description="Multi-account publishing and revenue optimization across every platform." 
              tag="GROWTH"
            />
          </motion.div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-bg-base/50">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-8 text-[11px] font-bold tracking-[0.2em] text-zinc-500 uppercase">
          <div className="flex items-center gap-3 opacity-50">
            <Zap className="h-5 w-5" />
            <span className="">Ettametta<span className="text-cyan-400">OS</span></span>
          </div>
          <div className="text-zinc-600">
            © 2026 ETTAMETTA_SYS. ALL RIGHTS RESERVED.
          </div>
        </div>
      </footer>
    </BaseLayout>
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
    <motion.div variants={itemVariants} className="surface-glass rounded-full border border-white/5 hover:border-cyan-400/30 transition-all group overflow-hidden relative p-8 text-center">
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <p className="text-4xl font-bold tracking-tight mb-2 text-white">{value}</p>
      <p className="text-[9px] font-bold uppercase tracking-[0.3em] text-zinc-500 group-hover:text-cyan-400 transition-colors">{label}</p>
    </motion.div>
  );
}

function StepCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div variants={itemVariants} className="surface-glass rounded-[3rem] border border-white/5 hover:border-cyan-500/30 transition-all text-left space-y-6 group p-10">
      <div className="h-16 w-16 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <div className="space-y-4">
        <h3 className="text-2xl font-bold uppercase tracking-tight text-white">{title}</h3>
        <p className="text-zinc-500 text-sm font-medium leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

function PortfolioCard({ icon, title, description, tag }: { icon: React.ReactNode, title: string, description: string, tag: string }) {
  return (
    <motion.div variants={itemVariants} className="surface-glass rounded-[3rem] border border-white/5 hover:border-cyan-400/30 transition-all text-left space-y-8 group relative overflow-hidden p-10">
       <div className="absolute top-6 right-6">
          <span className="text-[9px] font-bold px-3 py-1 bg-white/5 border border-white/10 rounded-full text-zinc-500 tracking-widest uppercase">{tag}</span>
       </div>
       <div className="h-20 w-20 rounded-full bg-white/3 border border-white/5 flex items-center justify-center group-hover:rotate-6 transition-all duration-500">
         {icon}
       </div>
       <div className="space-y-4">
         <h3 className="text-3xl font-bold uppercase tracking-tight text-white">{title}</h3>
         <p className="text-zinc-500 font-medium leading-relaxed">{description}</p>
       </div>
       <button className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-400 group-hover:gap-4 transition-all">
         INITIALIZE_DEEP_LINK <ArrowRight className="h-4 w-4" />
       </button>
     </motion.div>
  );
}
