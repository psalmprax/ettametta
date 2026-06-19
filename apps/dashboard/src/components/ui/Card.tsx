import React from "react";
import { cn } from "@/lib/utils";

/**
 * Module-internal — do not consume from outside.
 *
 * Props for the public `<Card>` element. Kept module-private so the
 * compound `Card` API owns the type contract — consumers should never need
 * to name `CardProps` explicitly.
 */
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "solid" | "elevated" | "subtle" | "accent";
  withBorder?: boolean;
  className?: string;
}

/**
 * Module-internal — do not consume from outside.
 *
 * The forwardRef core of the public `Card` component. Kept module-private so
 * the compound API (`<Card.Header>`, `<Card.Body>`, `<Card.Footer>`) owns the
 * surface — any future consumer must import `Card`, never `CardRoot` directly.
 */
const CardRoot = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "solid", withBorder = true, children, ...props }, ref) => {
    const baseStyles = "relative overflow-hidden transition-all duration-300 rounded-2xl";

    const variants = {
      solid: "bg-slate-900/50 border border-white/5 shadow-sm hover:border-white/10",
      elevated: "bg-slate-900 border border-white/10 shadow-lg",
      subtle: "bg-black/20 border border-white/5 hover:border-white/10",
      accent: "bg-cyan-400/5 border border-cyan-400/20 shadow-sm",
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          !withBorder && "border-none shadow-none",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
CardRoot.displayName = "Card";

/**
 * Module-internal — do not consume from outside.
 *
 * Semantic header section for a `<Card>`. Border-bottom separators and the
 * 24px padding rhythm are part of the compound surface. Reach it via
 * `<Card.Header>` rather than importing the bare const.
 */
const CardHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-b border-white/5", className)} {...props}>
    {children}
  </div>
);

/**
 * Module-internal — do not consume from outside.
 *
 * Body region of a `<Card>`. Reach via `<Card.Body>`. Stateless passthrough —
 * the boundary is purely visual.
 */
const CardBody = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6", className)} {...props}>
    {children}
  </div>
);

/**
 * Module-internal — do not consume from outside.
 *
 * Footer region of a `<Card>` (border-top, equal 24px padding). Reach via
 * `<Card.Footer>`.
 */
const CardFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-6 border-t border-white/5", className)} {...props}>
    {children}
  </div>
);

/**
 * Compound component API.
 *
 * `<Card>` renders the container; consumers compose sections via
 * `<Card.Header>` / `<Card.Body>` / `<Card.Footer>`:
 *
 *     <Card>
 *         <Card.Header>Title</Card.Header>
 *         <Card.Body>…</Card.Body>
 *         <Card.Footer>…</Card.Footer>
 *     </Card>
 *
 * `Object.assign` is the standard React pattern for this — it attaches the
 * subcomponents as static properties of the forwardRef component WITHOUT
 * changing the call signature. TypeScript infers
 *   (typeof CardRoot) & { Header: typeof CardHeader; Body: typeof CardBody; Footer: typeof CardFooter }
 * from the assignment expression, so JSX type-checks `<Card.Header>` etc.
 * Existing `<Card>` consumers continue to render via CardRoot unchanged.
 */
export const Card = Object.assign(CardRoot, {
  Header: CardHeader,
  Body: CardBody,
  Footer: CardFooter,
});
