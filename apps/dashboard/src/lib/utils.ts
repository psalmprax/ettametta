import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function safeRandomUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    // Fallback for non-secure contexts (HTTP)
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Robustly copies text to clipboard, handling non-secure contexts and older browsers.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
    // 1. Try modern navigator.clipboard API
    if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.warn("navigator.clipboard.writeText failed, falling back", err);
        }
    }

    // 2. Fallback to older document.execCommand('copy') approach
    try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        
        // Ensure textarea is not visible but part of DOM
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "0";
        document.body.appendChild(textArea);
        
        textArea.focus();
        textArea.select();
        
        const successful = document.execCommand("copy");
        document.body.removeChild(textArea);
        return successful;
    } catch (err) {
        console.error("Fallback clipboard copy failed", err);
        return false;
    }
}
export function formatLabel(label: string): string {
    if (!label) return "";
    return label
        .replace(/_/g, " ")
        .replace(/\b\w/g, (l) => l.toUpperCase());
}
