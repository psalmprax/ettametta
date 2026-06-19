"use client";

import React from "react";
import { PlusCircle, User, Mic2, Video, Fingerprint } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Persona } from "@/lib/types";

interface Props {
    personas: Persona[];
}

export default function IdentitiesTab({ personas }: Props) {
    return (
        <div className="space-y-8 h-full flex flex-col">
            <div className="flex items-center justify-between shrink-0">
                <h3 className="text-2xl font-bold text-white uppercase tracking-tighter">
                    Neural Identity Lab
                </h3>
                <Button className="bg-white/5 border border-white/10 hover:bg-white/10 text-white gap-2">
                    <PlusCircle className="h-4 w-4" /> Register New ID
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 overflow-y-auto custom-scrollbar p-1">
                {personas?.map((persona) => (
                    <div
                        key={persona.id ?? persona._id}
                        className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6 group hover:border-cyan-500/20 transition-all"
                    >
                        <div className="aspect-square rounded-2xl bg-zinc-900 overflow-hidden relative border border-white/5">
                            {persona.reference_image_uri ? (
                                <img
                                    src={persona.reference_image_uri}
                                    alt={persona.name}
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                    <User className="h-12 w-12 text-zinc-800" />
                                </div>
                            )}
                            <div className="absolute inset-0 bg-linear-to-t from-black/80 via-transparent to-transparent" />
                            <div className="absolute bottom-4 left-4">
                                <span className="text-[8px] font-bold text-cyan-400 uppercase tracking-widest px-2 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full">
                                    Active_ID
                                </span>
                            </div>
                        </div>
                        <div className="space-y-1">
                            <h4 className="text-lg font-bold text-white uppercase tracking-tight">
                                {persona.name}
                            </h4>
                            <p className="text-[10px] font-mono text-zinc-600">
                                ID: {persona.id ?? persona._id}
                            </p>
                        </div>
                        <div className="flex items-center justify-between pt-4 border-t border-white/5">
                            <div className="flex gap-2">
                                <div className="h-6 w-6 rounded bg-white/5 flex items-center justify-center">
                                    <Mic2 className="h-3 w-3 text-zinc-500" />
                                </div>
                                <div className="h-6 w-6 rounded bg-white/5 flex items-center justify-center">
                                    <Video className="h-3 w-3 text-zinc-500" />
                                </div>
                            </div>
                            <Button
                                variant="outline"
                                className="h-8 text-[9px] uppercase font-bold border-white/10 text-white hover:bg-cyan-500 hover:text-black"
                            >
                                Modify
                            </Button>
                        </div>
                    </div>
                ))}

                {personas.length === 0 && (
                    <div className="col-span-4 h-full flex flex-col items-center justify-center opacity-10 gap-6 py-20">
                        <Fingerprint className="h-24 w-24" />
                        <span className="text-xl font-black uppercase tracking-[1em]">
                            No Neural IDs Found
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}
