"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { Shield, LayoutDashboard, Users, Map, Building2, ClipboardCheck, ListTodo, FileText, Settings, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Clients', href: '/clients', icon: Users },
  { name: 'Estates', href: '/estates', icon: Map },
  { name: 'Sites', href: '/sites', icon: Building2 },
  { name: 'Assessments', href: '/assessments', icon: ClipboardCheck },
  { name: 'Actions', href: '/actions', icon: ListTodo },
  { name: 'Reports', href: '/reports', icon: FileText },
];

const ADMIN_ITEM = { name: 'Admin', href: '/admin', icon: Settings };

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: session } = useSession();

  const handleSignOut = () => {
    signOut({ callbackUrl: '/login' });
  };

  const navItems = session?.user?.role === 'Administrator' 
    ? [...NAV_ITEMS, ADMIN_ITEM] 
    : NAV_ITEMS;

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-secondary)]">
      {/* Sidebar */}
      <aside className="hidden w-64 overflow-y-auto border-r border-[var(--border-color)] bg-[var(--bg-primary)] px-4 py-6 md:block">
        <div className="flex items-center gap-3 px-2 mb-8">
          <Shield className="h-8 w-8 text-[var(--primary-500)]" />
          <span className="text-xl font-bold tracking-tight">DRISK</span>
        </div>
        
        <nav className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-[var(--primary-500)] text-white" 
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-[var(--border-color)] bg-[var(--bg-primary)] px-4 sm:px-6">
          <div className="flex items-center md:hidden">
             <Shield className="h-6 w-6 text-[var(--primary-500)] mr-2" />
             <span className="text-lg font-bold">DRISK</span>
          </div>

          <div className="flex flex-1 items-center justify-end gap-4">
             {/* Theme Toggle placeholder */}
             
             {/* User Menu */}
             <div className="flex items-center gap-4 border-l border-[var(--border-color)] pl-4">
               {session?.user && (
                 <div className="hidden flex-col items-end sm:flex">
                    <span className="text-sm font-medium">{session.user.name}</span>
                    <span className="text-xs text-[var(--text-secondary)]">{session.user.role}</span>
                 </div>
               )}
               <button 
                onClick={handleSignOut}
                className="rounded-full p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
                title="Sign out"
               >
                 <LogOut className="h-5 w-5" />
               </button>
             </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-[var(--container-xl)] w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
