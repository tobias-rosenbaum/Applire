import { AppSidebar } from "@/components/shell/AppSidebar";

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-surface-dim">
      <AppSidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
