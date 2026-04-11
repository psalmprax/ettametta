/**
 * Secure and resilient token retrieval with cross-storage fallback.
 * Essential for production stability where direct localStorage access is common.
 */
export function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    
    // Check sessionStorage first (preferred for security/session scope)
    let token = sessionStorage.getItem("et_token");
    if (!token) {
        // Fallback to localStorage
        token = localStorage.getItem("et_token");
    }
    
    // Fix null/undefined string bug for ALL storage paths
    if (!token || token === "null" || token === "undefined" || token.trim().length === 0) {
        return null;
    }
    
    return token;
}
