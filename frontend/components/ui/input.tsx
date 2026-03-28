import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-12 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-neutral-dark placeholder:text-gray-400 transition-colors duration-200",
          "focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50",
          error && "border-critical focus:border-critical focus:ring-critical/20",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };