import React from 'react'
import { render } from '@testing-library/react'
import { SWRConfig } from 'swr'

// Custom render function that includes providers
export function renderWithProviders(
  ui: React.ReactElement,
  options?: any
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <SWRConfig 
        value={{
          provider: () => new Map(),
          fetcher: () => Promise.resolve(null),
          dedupingInterval: 0,
          revalidateOnFocus: false
        }}
      >
        {children}
      </SWRConfig>
    )
  }

  return render(ui, { wrapper: Wrapper, ...options })
}

export * from '@testing-library/react'