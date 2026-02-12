export const MetricCard = ({ icon: Icon, label, value, subValue, variant = "cyan" }) => {
  const variants = {
    cyan: "from-teal-600 to-teal-500 border-teal-400",
    teal: "from-emerald-700 to-emerald-600 border-emerald-500",
    amber: "from-amber-700 to-amber-600 border-amber-500",
    purple: "from-violet-700 to-violet-600 border-violet-500",
    blue: "from-blue-700 to-blue-600 border-blue-500",
    rose: "from-rose-700 to-rose-600 border-rose-500"
  };

  return (
    <div className={`rounded-xl p-5 bg-gradient-to-br ${variants[variant]} border relative overflow-hidden`}>
      <div className="absolute top-0 right-0 w-20 h-20 bg-white/5 rounded-full -mr-10 -mt-10" />
      <Icon className="w-6 h-6 text-white/80 mb-2" />
      <p className="text-white/70 text-sm mb-1">{label}</p>
      <p className="text-white text-2xl font-bold">{value}</p>
      {subValue && <p className="text-white/60 text-xs mt-1">{subValue}</p>}
    </div>
  );
};

export default MetricCard;
