"use client";

export default function BrandPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-8 overflow-hidden relative">
      {/* Background Decorative Elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-clinical-info/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] animate-pulse delay-700" />
      
      <div className="relative z-10 flex flex-col items-center text-center">
        {/* Large Logo */}
        <div className="mb-12 relative group">
          <div className="absolute inset-0 bg-clinical-info/40 rounded-3xl blur-2xl group-hover:bg-clinical-info/60 transition-all duration-700 opacity-50" />
          <img 
            src="/logo.png" 
            alt="KairosMD Logo" 
            className="w-48 h-48 relative z-10 rounded-[2.5rem] shadow-[0_0_50px_rgba(37,99,235,0.3)] border border-white/20"
          />
        </div>

        {/* Title */}
        <h1 className="text-8xl font-black tracking-tighter mb-4">
          <span className="text-clinical-info drop-shadow-[0_0_20px_rgba(37,99,235,0.5)]">Kairos</span>
          <span className="text-white">MD</span>
        </h1>

        {/* Subtitle */}
        <p className="text-2xl font-bold text-slate-400 max-w-2xl leading-relaxed uppercase tracking-[0.2em]">
          Intelligent Clinical Decision Support
        </p>
        
        {/* Tagline */}
        <div className="mt-12 flex items-center gap-4 text-slate-500 font-medium">
          <div className="h-px w-12 bg-slate-800" />
          <span className="text-sm tracking-widest uppercase">Propelling Ward Rounds with AI + FHIR</span>
          <div className="h-px w-12 bg-slate-800" />
        </div>
      </div>

      {/* Bottom info */}
      <div className="absolute bottom-12 text-slate-600 text-xs font-bold uppercase tracking-widest">
        Built for the Multidisciplinary Team
      </div>
    </div>
  );
}
