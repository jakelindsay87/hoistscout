import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('utils', () => {
  it('cn should merge class names correctly', () => {
    expect(cn('class1', 'class2')).toContain('class1')
    expect(cn('class1', 'class2')).toContain('class2')
  })

  it('cn should handle conditional classes', () => {
    expect(cn('base', true && 'conditional')).toContain('conditional')
    expect(cn('base', false && 'conditional')).not.toContain('conditional')
  })
})