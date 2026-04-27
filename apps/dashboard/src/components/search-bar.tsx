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

    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                e.preventDefault();
                setIsOpen(true);
            }
            if (e.key === "Escape") {
                setIsOpen(false);
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

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
                                className="w-full h-11 pl-12 pr-10 bg-white border border-slate-200 rounded-xl text-slate-900 text-sm font-medium placeholder:text-slate-400 focus:outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-400/10 shadow-sm transition-all"
                                autoFocus
                            />
                        </form>
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                        <button
                            onClick={() => { setIsOpen(false); setQuery(""); }}
                            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                            <X className="h-4 w-4 text-slate-400" />
                        </button>
                    </motion.div>
                ) : (
                    <motion.button
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(true)}
                        className="flex items-center gap-2 h-10 px-4 bg-white border border-slate-200 rounded-xl text-slate-600 hover:text-slate-900 hover:border-slate-300 hover:shadow-sm transition-all"
                    >
                        <Search className="h-4 w-4 group-hover:scale-110 transition-transform" />
                        <span className="text-sm">Search...</span>
                        <kbd className="hidden lg:inline-flex items-center gap-1 h-5 px-2 bg-slate-100 rounded text-[10px] text-slate-500 font-semibold">
                            ⌘K
                        </kbd>
                    </motion.button>
                )}
            </AnimatePresence>
        </div>
    );
}
