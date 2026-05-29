type DigitPadProps = {
  onDigit: (d: number) => void
  onBackspace?: () => void
  onClear?: () => void
  className?: string
}

export default function DigitPad({ onDigit, onBackspace, onClear, className = '' }: DigitPadProps){
  const digits = [1,2,3,4,5,6,7,8,9,0]

  return (
    <div className={`digit-pad controls ${className}`}>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, maxWidth: 260}}>
        {digits.map((d) => (
          <button key={d} type="button" className="btn" onClick={() => onDigit(d)} aria-label={`digit-${d}`}>
            {d}
          </button>
        ))}
        <div style={{gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', marginTop: 6}}>
          <button type="button" className="btn secondary" onClick={onBackspace}>⌫</button>
          <button type="button" className="btn secondary" onClick={onClear}>清除</button>
        </div>
      </div>
    </div>
  )
}
