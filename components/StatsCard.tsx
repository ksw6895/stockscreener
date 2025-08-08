interface StatsCardProps {
  title: string
  value: string | number
  icon: string
  color: 'blue' | 'green' | 'purple' | 'yellow'
}

export default function StatsCard({ title, value, icon, color }: StatsCardProps) {
  const colorClasses = {
    blue: 'bg-gradient-to-r from-blue-500 to-blue-600',
    green: 'bg-gradient-to-r from-green-500 to-green-600',
    purple: 'bg-gradient-to-r from-purple-500 to-purple-600',
    yellow: 'bg-gradient-to-r from-yellow-500 to-yellow-600'
  }

  return (
    <div className={`${colorClasses[color]} rounded-xl p-6 text-white shadow-lg transform hover:scale-105 transition-transform duration-200`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        <span className="text-xs font-medium opacity-80 uppercase tracking-wider">{title}</span>
      </div>
      <div className="text-3xl font-bold">
        {value}
      </div>
    </div>
  )
}