import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Linkedin, Mail, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

type Department = 'leadership' | 'technical' | 'research' | 'operations' | 'partnerships';

interface TeamMember {
  name: string;
  nameKey: string;
  roleKey: string;
  bioKey: string;
  department: Department;
  initials: string;
  gradient: string;
  linkedin?: string;
  email?: string;
}

const teamMembers: TeamMember[] = [
  {
    name: 'Dr. Amara Diallo',
    nameKey: 'amara',
    roleKey: 'team.roles.ceo',
    bioKey: 'team.bios.amara',
    department: 'leadership',
    initials: 'AD',
    gradient: 'from-emerald-400 to-teal-600',
    linkedin: '#',
    email: 'amara@agriwatch.org',
  },
  {
    name: 'Kwame Asante',
    nameKey: 'kwame',
    roleKey: 'team.roles.cto',
    bioKey: 'team.bios.kwame',
    department: 'technical',
    initials: 'KA',
    gradient: 'from-blue-400 to-indigo-600',
    linkedin: '#',
  },
  {
    name: 'Fatou Ndiaye',
    nameKey: 'fatou',
    roleKey: 'team.roles.headResearch',
    bioKey: 'team.bios.fatou',
    department: 'research',
    initials: 'FN',
    gradient: 'from-purple-400 to-violet-600',
    linkedin: '#',
  },
  {
    name: 'Oluwaseun Adeyemi',
    nameKey: 'oluwaseun',
    roleKey: 'team.roles.fieldOps',
    bioKey: 'team.bios.oluwaseun',
    department: 'operations',
    initials: 'OA',
    gradient: 'from-orange-400 to-red-500',
    linkedin: '#',
  },
  {
    name: 'Grace Mwangi',
    nameKey: 'grace',
    roleKey: 'team.roles.partnerships',
    bioKey: 'team.bios.grace',
    department: 'partnerships',
    initials: 'GM',
    gradient: 'from-pink-400 to-rose-600',
    linkedin: '#',
  },
  {
    name: 'Ibrahim Traore',
    nameKey: 'ibrahim',
    roleKey: 'team.roles.mlLead',
    bioKey: 'team.bios.ibrahim',
    department: 'technical',
    initials: 'IT',
    gradient: 'from-cyan-400 to-blue-600',
    linkedin: '#',
  },
  {
    name: 'Aisha Mohammed',
    nameKey: 'aisha',
    roleKey: 'team.roles.agronomist',
    bioKey: 'team.bios.aisha',
    department: 'research',
    initials: 'AM',
    gradient: 'from-lime-400 to-green-600',
    linkedin: '#',
  },
  {
    name: 'Jean-Pierre Habimana',
    nameKey: 'jeanPierre',
    roleKey: 'team.roles.community',
    bioKey: 'team.bios.jeanPierre',
    department: 'operations',
    initials: 'JP',
    gradient: 'from-amber-400 to-orange-600',
    linkedin: '#',
  },
];

const departmentColors: Record<Department, string> = {
  leadership: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  technical: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  research: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  operations: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  partnerships: 'bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-300',
};

export function TeamSection() {
  const { t } = useTranslation();
  const [activeDepartment, setActiveDepartment] = useState<Department | 'all'>('all');

  const departments: { key: Department | 'all'; labelKey: string }[] = [
    { key: 'all', labelKey: 'team.departments.all' },
    { key: 'leadership', labelKey: 'team.departments.leadership' },
    { key: 'technical', labelKey: 'team.departments.technical' },
    { key: 'research', labelKey: 'team.departments.research' },
    { key: 'operations', labelKey: 'team.departments.operations' },
    { key: 'partnerships', labelKey: 'team.departments.partnerships' },
  ];

  const filteredMembers =
    activeDepartment === 'all'
      ? teamMembers
      : teamMembers.filter((m) => m.department === activeDepartment);

  return (
    <section id="team" className="relative py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 mb-4">
            {t('team.badge')}
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            {t('team.title')}{' '}
            <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
              {t('team.titleHighlight')}
            </span>
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            {t('team.subtitle')}
          </p>
        </motion.div>

        {/* Department Filter */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex flex-wrap justify-center gap-2 mb-12"
        >
          {departments.map((dept) => (
            <button
              key={dept.key}
              onClick={() => setActiveDepartment(dept.key)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                activeDepartment === dept.key
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/25'
                  : 'bg-white/80 dark:bg-gray-800/80 text-gray-600 dark:text-gray-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 border border-gray-200 dark:border-gray-700'
              }`}
            >
              {t(dept.labelKey)}
            </button>
          ))}
        </motion.div>

        {/* Team Grid */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeDepartment}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
          >
            {filteredMembers.map((member, index) => (
              <motion.div
                key={member.nameKey}
                custom={index}
                variants={fadeInUp}
                initial="hidden"
                animate="visible"
                className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-600 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-500/10 hover:-translate-y-1"
              >
                {/* Avatar */}
                <div className="flex items-center mb-4">
                  <div
                    className={`w-14 h-14 rounded-full bg-gradient-to-br ${member.gradient} flex items-center justify-center text-white font-bold text-lg shadow-lg`}
                  >
                    {member.initials}
                  </div>
                  <div className="ml-3 flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                      {t(`team.members.${member.nameKey}`)}
                    </h3>
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${departmentColors[member.department]}`}
                    >
                      {t(`team.departments.${member.department}`)}
                    </span>
                  </div>
                </div>

                {/* Role */}
                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400 mb-2">
                  {t(member.roleKey)}
                </p>

                {/* Bio */}
                <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed mb-4 line-clamp-3">
                  {t(member.bioKey)}
                </p>

                {/* Contact Links */}
                <div className="flex items-center gap-2 pt-3 border-t border-gray-100 dark:border-gray-700">
                  {member.linkedin && (
                    <a
                      href={member.linkedin}
                      className="p-2 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                      aria-label="LinkedIn"
                    >
                      <Linkedin className="w-4 h-4" />
                    </a>
                  )}
                  {member.email && (
                    <a
                      href={`mailto:${member.email}`}
                      className="p-2 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
                      aria-label="Email"
                    >
                      <Mail className="w-4 h-4" />
                    </a>
                  )}
                  <div className="flex-1" />
                  <ChevronRight className="w-4 h-4 text-gray-300 dark:text-gray-600 group-hover:text-emerald-500 transition-colors" />
                </div>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>

        {/* Join CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center gap-3 px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800">
            <User className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
              {t('team.joinCta')}
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
