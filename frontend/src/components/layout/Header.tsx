import { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Menu, Sun, Moon } from 'lucide-react';
import { Drawer } from '@/components/ui/Drawer';
import { IconButton } from '@/components/ui/IconButton';
import { Badge } from '@/components/ui/Badge';
import { MarketStatusIndicator } from './MarketStatusIndicator';
import { useThemePreference } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

export interface HeaderProps {
  apiStatus?: 'online' | 'offline' | 'checking';
  pipelineVersion?: string;
  asOfDate?: string;
  isStale?: boolean;
  favoritesCount?: number;
}

export const NAV_LINKS = [
  { to: '/', label: 'Overview' },
  { to: '/data', label: 'Data' },
  { to: '/events', label: 'Events' },
  { to: '/event-study', label: 'Event Study' },
  { to: '/methodology', label: 'Methodology' },
  { to: '/models', label: 'Model Lab' },
  { to: '/news', label: 'News' },
  { to: '/scenario', label: 'Scenario Predictor' },
  // { to: '/research', label: 'Research' },
  // { to: '/favorites', label: 'Favorites', isFavorites: true },
];

export function Header({
  pipelineVersion,
  asOfDate,
  isStale = false,
  favoritesCount = 0,
}: HeaderProps) {
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const { isDark, toggleTheme } = useThemePreference();

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-border bg-blue-navy text-white shadow-soft">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand Logo & Name */}
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="group flex items-center gap-2.5 rounded-button focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <div className="transition-standard flex h-8 w-8 items-center justify-center rounded-button bg-accent font-heading text-sm font-black text-accent-foreground shadow-soft group-hover:scale-105">
                CSE
              </div>
              <div className="flex flex-col leading-none">
                <span className="flex items-center gap-1.5 font-heading text-sm font-bold tracking-tight text-white">
                  CSE ASPI Political Event Study
                  {/* <span className="hidden rounded border border-white/20 bg-white/15 px-1.5 py-0.5 font-mono text-[10px] font-medium text-accent sm:inline-block">
                    SLIIT
                  </span> */}
                </span>
                <span className="hidden text-[10px] text-blue-soft sm:block">
                  Political Events & Econometrics
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation Links (>= 1024px) */}
          <nav
            aria-label="Primary Navigation"
            className="hidden items-center gap-1 font-sans text-xs font-medium lg:flex xl:gap-2"
          >
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'transition-standard flex items-center gap-1.5 rounded-button px-2.5 py-1.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
                    isActive
                      ? 'bg-white/15 font-semibold text-white shadow-soft'
                      : 'text-blue-soft hover:bg-white/10 hover:text-white'
                  )
                }
              >
                <span>{link.label}</span>
                {link.isFavorites && favoritesCount > 0 && (
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-accent font-mono text-[10px] font-bold text-accent-foreground">
                    {favoritesCount}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Right Header Toolbar: Theme Toggle, Connection Status, Mobile Menu Trigger */}
          <div className="flex items-center gap-2">
            {/* Real-time Stage 4 Market Data Stream Status Indicator */}
            <div className="hidden items-center border-r border-white/20 pr-2 sm:flex">
              <MarketStatusIndicator />
            </div>

            {/* Dark/Light Mode Toggle */}
            <IconButton
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              className="text-white hover:bg-white/10 hover:text-white"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </IconButton>

            {/* Mobile / Tablet Drawer Hamburger ( < 1024px) */}
            <IconButton
              variant="ghost"
              size="sm"
              onClick={() => setMobileDrawerOpen(true)}
              aria-label="Open navigation menu"
              className="text-white hover:bg-white/10 hover:text-white lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </IconButton>
          </div>
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      <Drawer
        isOpen={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
        title="Research Modules"
        description="Colombo Stock Exchange Political Econometrics"
        side="left"
      >
        <div className="space-y-4">
          <nav className="space-y-1" aria-label="Mobile Navigation">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === '/'}
                onClick={() => setMobileDrawerOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'transition-standard flex items-center justify-between rounded-button px-3 py-2.5 text-sm font-medium',
                    isActive
                      ? 'dark:bg-blue-soft/30 bg-blue-ice font-semibold text-blue-navy dark:text-blue-vibrant'
                      : 'text-text-muted hover:bg-surface-subtle hover:text-text-primary'
                  )
                }
              >
                <span>{link.label}</span>
                {link.isFavorites && (
                  <Badge variant="navy" size="sm">
                    {favoritesCount}
                  </Badge>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="border-border/60 space-y-1.5 border-t pt-4 font-mono text-xs text-text-muted">
            <div className="flex items-center justify-between pb-1">
              <span>Market Stream:</span>
              <MarketStatusIndicator />
            </div>
            {pipelineVersion && <div>Pipeline Version: {pipelineVersion}</div>}
            {asOfDate && <div>Data As-Of: {asOfDate}</div>}
            {isStale && <div className="font-semibold text-data-warning">Status: Data Stale</div>}
            <div className="pt-2 text-[11px] text-text-subtle">
              Permanent Rules FR1–FR10 Enforced
            </div>
            {import.meta.env.DEV && (
              <div className="border-border/60 mt-3 border-t pt-3">
                <div className="mb-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-accent">
                  Developer Tools (Dev Only)
                </div>
                <div className="flex flex-col gap-1">
                  <Link
                    to="/_contract"
                    onClick={() => setMobileDrawerOpen(false)}
                    className="font-mono text-xs text-accent hover:underline"
                  >
                    /_contract (API Contract Catalog)
                  </Link>
                  <Link
                    to="/_design"
                    onClick={() => setMobileDrawerOpen(false)}
                    className="font-mono text-xs text-accent hover:underline"
                  >
                    /_design (Design System Showcase)
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </Drawer>
    </>
  );
}
