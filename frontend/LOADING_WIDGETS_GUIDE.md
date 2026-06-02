# Loading Widgets Implementation Guide

## Overview
This frontend now includes a comprehensive loading widget system to enhance UX across all pages. The system consists of **full-page loaders** and **component-level loaders** with smooth spinner animations.

## Components Created

### 1. **LoadingSpinner** (`components/LoadingSpinner.tsx`)
The base spinner component with customizable sizes and modes.

**Props:**
- `size` - Spinner size: `'small' | 'medium' | 'large'` (default: `'medium'`)
- `fullPage` - Boolean to enable full-page overlay mode (default: `false`)
- `message` - Optional loading message text

**Usage Examples:**

```tsx
import LoadingSpinner from '@/components/LoadingSpinner'

// Inline spinner
<LoadingSpinner size="small" message="Processing..." />

// Full-page overlay
<LoadingSpinner fullPage={true} size="large" message="Loading..." />
```

### 2. **PageLoader** (`components/PageLoader.tsx`)
Full-page overlay loader for complete page loading states.

**Props:**
- `isLoading` - Boolean to control visibility (default: `false`)
- `message` - Custom loading message (default: `'Loading...'`)

**Usage Examples:**

```tsx
import PageLoader from '@/components/PageLoader'

export default function MyPage() {
  const [loading, setLoading] = useState(false)
  
  return (
    <>
      <PageLoader isLoading={loading} message="Loading data..." />
      {/* Page content */}
    </>
  )
}
```

### 3. **CardLoader** (`components/CardLoader.tsx`)
Component-level loader for individual cards and sections.

**Props:**
- `isLoading` - Boolean to control visibility
- `height` - Custom container height (default: `'300px'`)
- `children` - Content to show when not loading

**Usage Examples:**

```tsx
import CardLoader from '@/components/CardLoader'

export default function DataCard() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  
  return (
    <CardLoader isLoading={loading} height="400px">
      {data && <YourContent data={data} />}
    </CardLoader>
  )
}
```

## Pages Updated

### ✅ Dashboard (`pages/dashboard.tsx`)
- Replaced custom spinner with `PageLoader`
- Shows on initial load and authentication

### ✅ Portfolio (`pages/portfolio.tsx`)
- Replaced custom spinner with `PageLoader`
- Shows while loading portfolio data

### ✅ Goal Optimizer (`pages/goal-optimizer.tsx`)
- Replaced custom spinner with `PageLoader`
- Shows during portfolio and optimization initialization

## Design Features

### Spinner Animation
- **Dual-ring dual-directional animation** - Primary ring spins clockwise, secondary ring counter-clockwise
- **Color scheme** - Uses your CSS variables (`--primary-600`, `--accent-500`)
- **Smooth performance** - CSS-based animations (no JavaScript overhead)

### Full-Page Overlay
- **Semi-transparent backdrop** with 4px blur effect
- **Fixed positioning** to cover entire viewport
- **High z-index** (`z-50`) to stay above other content
- **Responsive** - Works on all screen sizes

## Integration Quick Reference

### For New Pages/Components

**Full-page loading:**
```tsx
import PageLoader from '@/components/PageLoader'

function MyPage() {
  const [loading, setLoading] = useState(true)
  
  return (
    <>
      <PageLoader isLoading={loading} message="Loading..." />
      {/* Rest of page */}
    </>
  )
}
```

**Section/Card loading:**
```tsx
import CardLoader from '@/components/CardLoader'

function DataSection() {
  const [loading, setLoading] = useState(true)
  
  return (
    <CardLoader isLoading={loading} height="250px">
      {/* Your content */}
    </CardLoader>
  )
}
```

## Styling Customization

The loaders use your existing CSS variables:
- `--primary-600` - Primary spinner color
- `--accent-500` - Secondary spinner color
- `--border-glass` - Card border
- `--text-secondary` - Label text color

To customize, modify the CSS variables in your global styles or override in component props.

## Best Practices

1. **Always show loader on initial load** - Set `isLoading={true}` by default
2. **Update message appropriately** - Use context-specific messages like "Loading portfolio..." or "Fetching data..."
3. **Handle errors gracefully** - Hide loader when complete, show error state
4. **Use PageLoader for critical paths** - Full page loads that block interaction
5. **Use CardLoader for sections** - Individual data fetches within a page
6. **Combine with error boundaries** - Have fallback UI if loading fails

## Example: Complete Integration

```tsx
import { useState, useEffect } from 'react'
import PageLoader from '@/components/PageLoader'

export default function MyPage() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const res = await fetch('/api/data')
        const result = await res.json()
        setData(result)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  if (error) return <div className="error">{error}</div>

  return (
    <>
      <PageLoader isLoading={loading} message="Loading..." />
      {data && <YourContent data={data} />}
    </>
  )
}
```

## Browser Compatibility

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

The loaders use standard CSS animations and are fully responsive.
