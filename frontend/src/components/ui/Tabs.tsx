import React, { createContext, useContext, useState } from 'react';
import { cn } from '@/lib/utils';

export interface TabItem {
  key: string;
  label: string;
  icon?: React.ReactNode | React.ElementType;
}

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (val: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

export interface TabsProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> {
  defaultValue?: string;
  value?: string;
  activeKey?: string;
  onValueChange?: (val: string) => void;
  onChange?: (val: string) => void;
  items?: TabItem[];
}

export function Tabs({
  defaultValue = '',
  value,
  activeKey,
  onValueChange,
  onChange,
  items,
  className,
  children,
  ...props
}: TabsProps) {
  const effectiveDefault = defaultValue || (items && items[0]?.key) || '';
  const [active, setActive] = useState(effectiveDefault);

  const controlledValue = value !== undefined ? value : activeKey;
  const currentTab = controlledValue !== undefined ? controlledValue : active;

  const handleTabChange = (val: string) => {
    if (controlledValue === undefined) setActive(val);
    onValueChange?.(val);
    onChange?.(val);
  };

  return (
    <TabsContext.Provider value={{ activeTab: currentTab, setActiveTab: handleTabChange }}>
      <div className={cn('space-y-4', className)} {...props}>
        {items ? (
          <TabList>
            {items.map((item) => {
              let iconNode: React.ReactNode = null;
              if (item.icon) {
                if (React.isValidElement(item.icon)) {
                  iconNode = item.icon;
                } else if (typeof item.icon === 'function' || typeof item.icon === 'object') {
                  const IconComp = item.icon as React.ElementType;
                  iconNode = <IconComp className="h-4 w-4 shrink-0" />;
                }
              }
              return (
                <TabTrigger key={item.key} value={item.key}>
                  <span className="inline-flex items-center gap-2">
                    {iconNode}
                    <span>{item.label}</span>
                  </span>
                </TabTrigger>
              );
            })}
          </TabList>
        ) : null}
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export function TabList({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex w-full items-center gap-1 border-b border-border pb-px text-sm font-medium',
        className
      )}
      {...props}
    />
  );
}

export interface TabTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

export function TabTrigger({ value, className, children, ...props }: TabTriggerProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('TabTrigger must be used within Tabs');

  const isActive = context.activeTab === value;

  return (
    <button
      role="tab"
      type="button"
      aria-selected={isActive}
      onClick={() => context.setActiveTab(value)}
      className={cn(
        'transition-standard -mb-px border-b-2 px-4 py-2 font-sans text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent sm:text-sm',
        isActive
          ? 'border-blue-cobalt font-semibold text-blue-navy dark:border-blue-vibrant dark:text-blue-vibrant'
          : 'border-transparent text-text-muted hover:border-border hover:text-text-primary',
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export interface TabContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}

export function TabContent({ value, className, children, ...props }: TabContentProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('TabContent must be used within Tabs');

  if (context.activeTab !== value) return null;

  return (
    <div
      role="tabpanel"
      tabIndex={0}
      className={cn('animate-fade-in focus-visible:outline-none', className)}
      {...props}
    >
      {children}
    </div>
  );
}

export const TabsList = TabList;
export const TabsTrigger = TabTrigger;
export const TabsContent = TabContent;
