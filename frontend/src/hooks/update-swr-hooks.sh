#!/bin/bash

# Update all SWR hooks to use the config
for file in useCredentials.ts useJobs.ts useOpportunities.ts useResults.ts useStats.ts; do
  echo "Updating $file..."
  
  # Add import if not present
  if ! grep -q "useSwrConfig" "$file"; then
    sed -i '1a import { useSwrConfig } from '\''./useSwrConfig'\''' "$file"
  fi
  
  # Update useSWR calls to include config
  sed -i 's/useSWR<\([^>]*\)>(\([^,]*\), \([^)]*\))/useSWR<\1>(\2, \3, swrConfig)/g' "$file"
  sed -i 's/useSWR(\([^,]*\), \([^)]*\))/useSWR(\1, \2, swrConfig)/g' "$file"
  
  # Add const swrConfig = useSwrConfig() at the beginning of functions
  sed -i '/export function use[A-Z]/ {
    n
    /const swrConfig/!s/^/  const swrConfig = useSwrConfig()\n/
  }' "$file"
done