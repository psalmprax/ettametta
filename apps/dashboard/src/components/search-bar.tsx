"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function SearchBar() {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState("");
    const router = useRouter();

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/discovery?q=${encodeURIComponent(query)}`);
            setQuery("");
            setIsOpen(false);
        }
    };

    return (
        <div className="relative hidden md:block">
            <AnimatePresence>
                {isOpen ? (
                    <motion.div
                        initial={{ width: 40, opacity: 0 }}
                        animate={{ width: 400, opacity: 1 }}
                        exit={{ width: 40, opacity: 0 }}
                        className="relative"
                    >
                        <form onSubmit={handleSearch}>
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Search trends, content, campaigns..."
                                className="w-full h-10 pl-12 pr-10 bg-zinc-900/80 border border-zinc-800 rounded-xl text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all"
                                autoFocus
                            />
                        </form>
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                        <button
                            onClick={() => { setIsOpen(false); setQuery(""); }}
                            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-zinc-800 rounded-lg transition-colors"
                        >
                            <X className="h-4 w-4 text-zinc-500" />
                        </button>
                    </motion.div>
                ) : (
                    <motion.button
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(true)}
                        className="flex items-center gap-2 h-10 px-4 bg-zinc-900/50 border border-zinc-800/50 rounded-xl text-zinc-500 hover:text-zinc-300 hover:border-zinc-700/50 transition-all group"
                    >
                        <Search className="h-4 w-4 group-hover:scale-110 transition-transform" />
                        <span className="text-sm">Search...</span>
                        <kbd className="hidden lg:inline-flex items-center gap-1 h-5 px-2 bg-zinc-800/50 rounded text-[10px] text-zinc-500 font-mono">
                            ⌘K
                        </kbd>
                    </motion.button>
                )}
            </AnimatePresence>
        </div>
    );
}
