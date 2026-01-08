import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [selectedTech, setSelectedTech] = useState('');
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  const technologies = [
    { value: 'AI Engineer', icon: '🤖', label: 'AI / ML', color: '#667eea' },
    { value: 'Data Scientist', icon: '📊', label: 'Data Science', color: '#f093fb' },
    { value: 'Data Analyst', icon: '📈', label: 'Data Analytics', color: '#4facfe' },
    { value: 'MERN Stack Developer', icon: '⚛️', label: 'MERN Stack', color: '#43e97b' },
    { value: 'Cloud Engineer', icon: '☁️', label: 'Cloud Computing', color: '#667eea' },
    { value: 'Cybersecurity Engineer', icon: '🔒', label: 'Cybersecurity', color: '#f5576c' },
    { value: 'Network Engineer', icon: '🌐', label: 'Networking', color: '#4facfe' },
    { value: 'Software Engineer', icon: '💻', label: 'Software Eng', color: '#764ba2' }
  ];

  const handleStartInterview = (tech) => {
    setSelectedTech(tech);
    localStorage.setItem('selectedTech', tech);
    navigate('/interview');
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header glass-card">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="url(#gradient-logo)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="url(#gradient-logo)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="url(#gradient-logo)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <defs>
                  <linearGradient id="gradient-logo" x1="2" y1="2" x2="22" y2="22">
                    <stop offset="0%" stopColor="#667eea"/>
                    <stop offset="100%" stopColor="#764ba2"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span className="logo-text">AI Interviewer</span>
          </div>

          <div className="header-actions">
            <div className="user-info">
              <div className="user-avatar">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="user-name">{user?.name || 'User'}</span>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 17L21 12L16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="dashboard-main">
        <div className="container">
          {/* Welcome Section */}
          <section className="welcome-section fade-in">
            <h1>Welcome back, {user?.name?.split(' ')[0] || 'there'}! 👋</h1>
            <p className="welcome-subtitle">Ready to ace your next interview? Choose a technology and let's get started.</p>
          </section>

          {/* Stats Cards */}
          <section className="stats-section">
            <div className="stats-grid">
              <div className="stat-card glass-card fade-in" style={{ animationDelay: '0.1s' }}>
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 11L12 14L22 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <div className="stat-content">
                  <h3>0</h3>
                  <p>Interviews Completed</p>
                </div>
              </div>

              <div className="stat-card glass-card fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <div className="stat-content">
                  <h3>-</h3>
                  <p>Average Score</p>
                </div>
              </div>

              <div className="stat-card glass-card fade-in" style={{ animationDelay: '0.3s' }}>
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 20V10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M18 20V4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M6 20V16" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <div className="stat-content">
                  <h3>0</h3>
                  <p>Technologies Practiced</p>
                </div>
              </div>
            </div>
          </section>

          {/* Technology Selection */}
          <section className="tech-selection-section">
            <h2>Choose Your Interview Topic</h2>
            <p className="section-subtitle">Select a technology stack or domain to begin your AI-powered interview</p>

            <div className="tech-grid">
              {technologies.map((tech, index) => (
                <div
                  key={tech.value}
                  className="tech-card glass-card fade-in"
                  style={{ animationDelay: `${0.1 * (index + 1)}s` }}
                  onClick={() => handleStartInterview(tech.value)}
                >
                  <div className="tech-card-icon" style={{ background: tech.color }}>
                    {tech.icon}
                  </div>
                  <h3>{tech.label}</h3>
                  <button className="btn btn-primary btn-sm">
                    Start Interview
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>

            {/* Custom Technology Input */}
            <div className="custom-tech-section glass-card">
              <h3>Or enter a custom topic</h3>
              <div className="custom-tech-input-group">
                <input
                  type="text"
                  placeholder="e.g., Rust, Go, Machine Learning, DevOps..."
                  value={selectedTech}
                  onChange={(e) => setSelectedTech(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && selectedTech.trim()) {
                      handleStartInterview(selectedTech);
                    }
                  }}
                />
                <button
                  className="btn btn-primary"
                  onClick={() => selectedTech.trim() && handleStartInterview(selectedTech)}
                  disabled={!selectedTech.trim()}
                >
                  Start Custom Interview
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
