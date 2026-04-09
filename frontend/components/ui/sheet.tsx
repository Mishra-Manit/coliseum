"use client";

import * as React from "react";
import { XIcon } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { Dialog as SheetPrimitive } from "radix-ui";

import { cn } from "@/lib/utils";

const sheetTransition = {
  duration: 0.24,
  ease: [0.22, 1, 0.36, 1] as const,
};

const SheetOpenContext = React.createContext<{ open: boolean }>({
  open: false,
});

const sideClasses = {
  top: "inset-x-0 top-0 w-full border-b",
  right: "inset-y-0 right-0 h-full w-3/4 border-l sm:max-w-sm",
  bottom: "inset-x-0 bottom-0 w-full border-t",
  left: "inset-y-0 left-0 h-full w-3/4 border-r sm:max-w-sm",
} as const;

function getSheetAnimation(side: keyof typeof sideClasses, reducedMotion: boolean) {
  if (reducedMotion) {
    return { opacity: 1, x: 0, y: 0 };
  }

  switch (side) {
    case "left":
      return { opacity: 0, x: -20, y: 0 };
    case "right":
      return { opacity: 0, x: 20, y: 0 };
    case "top":
      return { opacity: 0, x: 0, y: -16 };
    case "bottom":
      return { opacity: 0, x: 0, y: 16 };
  }
}

function Sheet({
  open: openProp,
  defaultOpen,
  onOpenChange,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Root>) {
  const isControlled = openProp !== undefined;
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(
    defaultOpen ?? false,
  );
  const open = openProp ?? uncontrolledOpen;

  const handleOpenChange = React.useCallback(
    (nextOpen: boolean) => {
      if (!isControlled) {
        setUncontrolledOpen(nextOpen);
      }
      onOpenChange?.(nextOpen);
    },
    [isControlled, onOpenChange],
  );

  return (
    <SheetOpenContext.Provider value={{ open }}>
      <SheetPrimitive.Root
        data-slot="sheet"
        open={open}
        onOpenChange={handleOpenChange}
        {...props}
      />
    </SheetOpenContext.Provider>
  );
}

function SheetTrigger({
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Trigger>) {
  return <SheetPrimitive.Trigger data-slot="sheet-trigger" {...props} />;
}

function SheetClose({
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Close>) {
  return <SheetPrimitive.Close data-slot="sheet-close" {...props} />;
}

function SheetPortal({
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Portal>) {
  return <SheetPrimitive.Portal data-slot="sheet-portal" {...props} />;
}

function SheetOverlay({
  className,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Overlay>) {
  const { open } = React.useContext(SheetOpenContext);
  const shouldReduceMotion = useReducedMotion() ?? false;

  return (
    <SheetPrimitive.Overlay forceMount asChild {...props}>
      <motion.div
        data-slot="sheet-overlay"
        initial={false}
        animate={{ opacity: open ? 1 : 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : sheetTransition}
        className={cn(
          "fixed inset-0 z-50 bg-black/48",
          !open && "pointer-events-none",
          className,
        )}
      />
    </SheetPrimitive.Overlay>
  );
}

function SheetContent({
  className,
  children,
  side = "right",
  showCloseButton = true,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Content> & {
  side?: "top" | "right" | "bottom" | "left";
  showCloseButton?: boolean;
}) {
  const { open } = React.useContext(SheetOpenContext);
  const shouldReduceMotion = useReducedMotion() ?? false;

  return (
    <SheetPortal>
      <SheetOverlay />
      <SheetPrimitive.Content
        forceMount
        data-slot="sheet-content"
        className="fixed inset-0 z-50 outline-hidden pointer-events-none"
        {...props}
      >
        <motion.div
          initial={false}
          animate={open ? { opacity: 1, x: 0, y: 0 } : getSheetAnimation(side, shouldReduceMotion)}
          transition={shouldReduceMotion ? { duration: 0 } : sheetTransition}
          className={cn(
            "bg-background pointer-events-auto absolute flex flex-col gap-4 shadow-2xl shadow-black/15",
            sideClasses[side],
            className,
          )}
        >
          {children}
          {showCloseButton && (
            <SheetPrimitive.Close className="ring-offset-background focus:ring-ring absolute top-4 right-4 rounded-xs opacity-70 transition-colors hover:bg-secondary hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none">
              <XIcon className="size-4" />
              <span className="sr-only">Close</span>
            </SheetPrimitive.Close>
          )}
        </motion.div>
      </SheetPrimitive.Content>
    </SheetPortal>
  );
}

function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-header"
      className={cn("flex flex-col gap-1.5 p-4", className)}
      {...props}
    />
  );
}

function SheetFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sheet-footer"
      className={cn("mt-auto flex flex-col gap-2 p-4", className)}
      {...props}
    />
  );
}

function SheetTitle({
  className,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Title>) {
  return (
    <SheetPrimitive.Title
      data-slot="sheet-title"
      className={cn("text-foreground font-semibold", className)}
      {...props}
    />
  );
}

function SheetDescription({
  className,
  ...props
}: React.ComponentProps<typeof SheetPrimitive.Description>) {
  return (
    <SheetPrimitive.Description
      data-slot="sheet-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props}
    />
  );
}

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
};
