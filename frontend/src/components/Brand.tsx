type BrandProps = {
  compact?: boolean
}

export function Brand({ compact = false }: BrandProps) {
  return (
    <span className={`brand ${compact ? 'brand-compact' : ''}`}>
      <img src="/brand/ennova-logo.jpg" alt="" className="brand-logo" />
      {!compact && <span className="brand-name">ENNOVA</span>}
    </span>
  )
}
