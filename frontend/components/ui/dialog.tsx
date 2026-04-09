"use client";

import * as React from "react";
import { XIcon } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { Dialog as DialogPrimitive } from "radix-ui";

import { cn } from "@/lib/utils";

const dialogTransition = {
  duration: 0.2,
  ease: [0.22, 1, 0.36, 1] as const,
};

const DialogOpenContext = React.createContext<{ open: boolean }>({
  open: false,
});

function Dialog({
  open: openProp,
  defaultOpen,
  onOpenChange,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Root>) {
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
    <DialogOpenContext.Provider value={{ open }}>
      <DialogPrimitive.Root
        data-slot="dialog"
        open={open}
        onOpenChange={handleOpenChange}
        {...props}
      />
    </DialogOpenContext.Provider>
  );
}

function DialogTrigger({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogClose({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />;
}

function DialogPortal({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />;
}

function DialogOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  const { open } = React.useContext(DialogOpenContext);
  const shouldReduceMotion = useReducedMotion() ?? false;

  return (
    <DialogPrimitive.Overlay forceMount asChild {...props}>
      <motion.div
        data-slot="dialog-overlay"
        initial={false}
        animate={{ opacity: open ? 1 : 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : dialogTransition}
        className={cn(
          "fixed inset-0 z-50 bg-black/52",
          !open && "pointer-events-none",
          className,
        )}
      />
    </DialogPrimitive.Overlay>
  );
}

function DialogContent({
  className,
  children,
  showCloseButton = true,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & {
  showCloseButton?: boolean;
}) {
  const { open } = React.useContext(DialogOpenContext);
  const shouldReduceMotion = useReducedMotion() ?? false;

  return (
    <DialogPortal forceMount>
      <DialogOverlay />
      <DialogPrimitive.Content
        forceMount
        data-slot="dialog-content"
        className="fixed inset-0 z-50 grid place-items-center p-4 outline-hidden pointer-events-none"
        {...props}
      >
        <motion.div
          initial={false}
          animate={
            open
              ? { opacity: 1, y: 0, scale: 1 }
              : {
                  opacity: 0,
                  y: shouldReduceMotion ? 0 : 8,
                  scale: shouldReduceMotion ? 1 : 0.985,
                }
          }
          transition={shouldReduceMotion ? { duration: 0 } : dialogTransition}
          className={cn(
            "bg-card relative w-full max-w-lg shadow-2xl shadow-black/15",
            open ? "pointer-events-auto" : "pointer-events-none",
            className,
          )}
        >
          {children}
          {showCloseButton && (
            <DialogPrimitive.Close className="ring-offset-background focus:ring-ring absolute top-4 right-4 rounded-xs opacity-70 transition-colors hover:bg-secondary hover:opacity-100 focus:ring-2 focus:ring-offset-2 focus:outline-hidden disabled:pointer-events-none">
              <XIcon className="size-4" />
              <span className="sr-only">Close</span>
            </DialogPrimitive.Close>
          )}
        </motion.div>
      </DialogPrimitive.Content>
    </DialogPortal>
  );
}

function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-header"
      className={cn("flex flex-col gap-1.5", className)}
      {...props}
    />
  );
}

function DialogTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn("text-foreground font-semibold", className)}
      {...props}
    />
  );
}

function DialogDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn("text-muted-foreground text-sm", className)}
      {...props}
    />
  );
}

export {
  Dialog,
  DialogTrigger,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
};
