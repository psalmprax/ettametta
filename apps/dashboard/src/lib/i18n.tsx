'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type TranslationKey = string;
type Translations = Record<TranslationKey, string>;

const translations: Record<string, Translations> = {
  en: {
    // Common
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
    
    // Auth
    'auth.login': 'Login',
    'auth.register': 'Register',
    'auth.logout': 'Logout',
    'auth.email': 'Email',
    'auth.password': 'Password',
    'auth.forgot_password': 'Forgot password?',
    'auth.no_account': "Don't have an account?",
    
    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.discovery': 'Discovery',
    'nav.creation': 'Creation',
    'nav.publishing': 'Publishing',
    'nav.analytics': 'Analytics',
    'nav.empire': 'Empire',
    'nav.settings': 'Settings',
    
    // Discovery
    'discovery.search_placeholder': 'Search for trends...',
    'discovery.trending': 'Trending',
    'discovery.niches': 'Niches',
    'discovery.viral_score': 'Viral Score',
    
    // Video
    'video.transform': 'Transform to Video',
    'video.generate': 'Generate Video',
    'video.rendering': 'Rendering...',
    
    // Publishing
    'publish.connect': 'Connect Account',
    'publish.schedule': 'Schedule Post',
    'publish.history': 'Publishing History',
    
    // Credits
    'credits.balance': 'Credits Balance',
    'credits.buy': 'Buy Credits',
    'credits.plan': 'Subscription Plan',
  },
  es: {
    'common.save': 'Guardar',
    'common.cancel': 'Cancelar',
    'common.delete': 'Eliminar',
    'common.edit': 'Editar',
    'common.loading': 'Cargando...',
    'common.error': 'Error',
    'common.success': 'Éxito',
    
    'auth.login': 'Iniciar sesión',
    'auth.register': 'Registrarse',
    'auth.logout': 'Cerrar sesión',
    'auth.email': 'Correo electrónico',
    'auth.password': 'Contraseña',
    
    'nav.dashboard': 'Panel',
    'nav.discovery': 'Descubrimiento',
    'nav.creation': 'Creación',
    'nav.publishing': 'Publicación',
    'nav.analytics': 'Analíticas',
    'nav.empire': 'Imperio',
    'nav.settings': 'Configuración',
  },
  fr: {
    'common.save': 'Enregistrer',
    'common.cancel': 'Annuler',
    'common.delete': 'Supprimer',
    'common.edit': 'Modifier',
    'common.loading': 'Chargement...',
    'common.error': 'Erreur',
    'common.success': 'Succès',
    
    'auth.login': 'Connexion',
    'auth.register': "S'inscrire",
    'auth.logout': 'Déconnexion',
    'auth.email': 'E-mail',
    'auth.password': 'Mot de passe',
    
    'nav.dashboard': 'Tableau de bord',
    'nav.discovery': 'Découverte',
    'nav.creation': 'Création',
    'nav.publishing': 'Publication',
    'nav.analytics': 'Analytique',
    'nav.empire': 'Empire',
    'nav.settings': 'Paramètres',
  },
  de: {
    'common.save': 'Speichern',
    'common.cancel': 'Abbrechen',
    'common.delete': 'Löschen',
    'common.edit': 'Bearbeiten',
    'common.loading': 'Laden...',
    'common.error': 'Fehler',
    'common.success': 'Erfolg',
    
    'auth.login': 'Anmelden',
    'auth.register': 'Registrieren',
    'auth.logout': 'Abmelden',
    'auth.email': 'E-Mail',
    'auth.password': 'Passwort',
    
    'nav.dashboard': 'Dashboard',
    'nav.discovery': 'Entdeckung',
    'nav.creation': 'Erstellung',
    'nav.publishing': 'Veröffentlichung',
    'nav.analytics': 'Analytik',
    'nav.empire': 'Reich',
    'nav.settings': 'Einstellungen',
  }
};

interface I18nContextType {
  locale: string;
  setLocale: (locale: string) => void;
  t: (key: string, params?: Record<string, string>) => string;
  availableLocales: string[];
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children }: { readonly children: ReactNode }) {
  const [locale, setLocale] = useState('en');

  useEffect(() => {
    const savedLocale = localStorage.getItem('locale');
    if (savedLocale && translations[savedLocale]) {
      setLocale(savedLocale);
    }
  }, []);

  const handleSetLocale = (newLocale: string) => {
    if (translations[newLocale]) {
      setLocale(newLocale);
      localStorage.setItem('locale', newLocale);
      document.documentElement.lang = newLocale;
    }
  };

  const t = (key: string, params?: Record<string, string>): string => {
    let text = translations[locale]?.[key] || translations['en']?.[key] || key;
    
    if (params) {
      Object.entries(params).forEach(([paramKey, value]) => {
        text = text.replace(new RegExp(`{{${paramKey}}}`, 'g'), value);
      });
    }
    
    return text;
  };

  return (
    <I18nContext.Provider value={{ 
      locale, 
      setLocale: handleSetLocale, 
      t, 
      availableLocales: Object.keys(translations) 
    }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}

export function LanguageSwitcher() {
  const { locale, setLocale, availableLocales } = useI18n();
  
  const localeNames: Record<string, string> = {
    en: 'English',
    es: 'Español',
    fr: 'Français',
    de: 'Deutsch'
  };

  return (
    <select
      value={locale}
      onChange={(e) => setLocale(e.target.value)}
      className="bg-zinc-800 text-white px-2 py-1 rounded border border-zinc-700"
      aria-label="Select language"
    >
      {availableLocales.map((loc) => (
        <option key={loc} value={loc}>
          {localeNames[loc] || loc}
        </option>
      ))}
    </select>
  );
}