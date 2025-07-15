import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * Optional label to display above the input.
   */
  label?: string;
  /**
   * Optional icon to display on the left side of the input.
   */
  icon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", label, icon, ...props }, ref) => {
    return (
      <div className="space-y-1">
        {/* Optional label */}
        {label && (
          <label className="block text-sm font-medium text-white/80">
            {label}
          </label>
        )}

        <div className="relative">
          {/* Optional icon */}
          {icon && (
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-white/50">
              {icon}
            </div>
          )}

          <input
            ref={ref}
            type={type}
            className={cn(
              "w-full rounded-md border border-black/20 bg-transparent py-2 pl-10 pr-4 text-sm text-black",
              "focus:outline-none  focus-visible:ring-offset-transparent",
              "disabled:cursor-not-allowed disabled:opacity-50",
              !icon && "pl-4",
              className
            )}
            {...props}
          />
        </div>
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
