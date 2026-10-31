import React from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import type { BreadcrumbItem } from '@/components/ui/Breadcrumbs';
import { cn } from '@/lib/utils';

export interface PageContainerProps {
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function PageContainer({
  title,
  description,
  breadcrumbs,
  badge,
  actions,
  children,
  className,
}: PageContainerProps) {
  return (
    <div className={cn('mx-auto w-full max-w-7xl flex-1 space-y-6 p-4 sm:p-6 lg:p-8', className)}>
      <PageHeader
        title={title}
        description={description}
        breadcrumbs={breadcrumbs}
        badge={badge}
        actions={actions}
      />
      <div>{children}</div>
    </div>
  );
}
