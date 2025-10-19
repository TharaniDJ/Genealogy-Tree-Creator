"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/hooks/useAuth';
import AuthGuard from '@/components/AuthGuard';
import VerticalNavbar from '@/components/VerticalNavbar';

interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
}

const AccountPage = () => {
  const router = useRouter();
  const { getToken, logout } = useAuth();
  
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'danger'>('profile');
  
  // Profile edit state
  const [editingProfile, setEditingProfile] = useState(false);
  const [newFullName, setNewFullName] = useState('');
  
  // Email change state
  const [changingEmail, setChangingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  
  // Password change state
  const [changingPassword, setChangingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // UI state
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Fetch user profile
  const fetchProfile = async () => {
    setLoading(true);
    try {
      const token = getToken();
      if (!token) {
        router.push('/login');
        return;
      }

      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      const response = await fetch(`${apiBase}/api/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      const data = await response.json();
      setProfile(data);
      setNewFullName(data.full_name || '');
    } catch (error) {
      console.error('Error fetching profile:', error);
      setError('Failed to load profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update profile (name)
  const handleUpdateProfile = async () => {
    setError('');
    setSuccess('');
    setActionLoading(true);

    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/me/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ full_name: newFullName })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      const updatedProfile = await response.json();
      setProfile(updatedProfile);
      setEditingProfile(false);
      setSuccess('Profile updated successfully!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update profile');
    } finally {
      setActionLoading(false);
    }
  };

  // Update email
  const handleUpdateEmail = async () => {
    setError('');
    setSuccess('');
    setActionLoading(true);

    if (!newEmail || !newEmail.includes('@')) {
      setError('Please enter a valid email address');
      setActionLoading(false);
      return;
    }

    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/me/email`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_email: newEmail })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update email');
      }

      const updatedProfile = await response.json();
      setProfile(updatedProfile);
      setChangingEmail(false);
      setNewEmail('');
      setSuccess('Email updated successfully!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update email');
    } finally {
      setActionLoading(false);
    }
  };

  // Update password
  const handleUpdatePassword = async () => {
    setError('');
    setSuccess('');
    setActionLoading(true);

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      setActionLoading(false);
      return;
    }

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters');
      setActionLoading(false);
      return;
    }

    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/me/password`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          current_password: currentPassword, 
          new_password: newPassword 
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update password');
      }

      setChangingPassword(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setSuccess('Password updated successfully!');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update password');
    } finally {
      setActionLoading(false);
    }
  };

  // Delete account
  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently deleted.'
    );

    if (!confirmed) return;

    const doubleConfirm = window.confirm(
      'This is your final warning. Your account and all associated data will be permanently deleted. Are you absolutely sure?'
    );

    if (!doubleConfirm) return;

    setError('');
    setActionLoading(true);

    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/me`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete account');
      }

      // Logout and redirect
      logout();
      router.push('/login?message=Account deleted successfully');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete account');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-[#0E0F19] flex items-center justify-center">
        <VerticalNavbar />
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#0E0F19] relative overflow-hidden">
      {/* Vertical Navbar */}
      <VerticalNavbar />
      
      {/* Animated gradient background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute top-0 -left-4 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Header */}
      <div className="relative backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-[#6B72FF] via-[#8B7BFF] to-[#6B72FF] bg-clip-text text-transparent">
                Account Settings
              </h1>
              <p className="text-gray-400 mt-1">Manage your account preferences and security</p>
            </div>
            <button
              onClick={() => router.push('/select')}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-white transition-all duration-200"
            >
              ← Back
            </button>
          </div>
        </div>
      </div>

      <div className="relative max-w-5xl mx-auto px-6 py-8">
        {/* Success/Error Messages */}
        {success && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400">
            {success}
          </div>
        )}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 flex gap-4 backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-2">
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              activeTab === 'profile'
                ? 'bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              activeTab === 'security'
                ? 'bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Security
          </button>
          <button
            onClick={() => setActiveTab('danger')}
            className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              activeTab === 'danger'
                ? 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Danger Zone
          </button>
        </div>

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            {/* Full Name */}
            <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">Full Name</h3>
                  <p className="text-gray-400 text-sm mt-1">Update your display name</p>
                </div>
                {!editingProfile && (
                  <button
                    onClick={() => setEditingProfile(true)}
                    className="px-4 py-2 bg-[#6B72FF] hover:bg-[#5a61db] text-white rounded-lg transition-all duration-200"
                  >
                    Edit
                  </button>
                )}
              </div>
              
              {editingProfile ? (
                <div className="space-y-4">
                  <input
                    type="text"
                    value={newFullName}
                    onChange={(e) => setNewFullName(e.target.value)}
                    placeholder="Enter your full name"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6B72FF] transition-all duration-200"
                  />
                  <div className="flex gap-3">
                    <button
                      onClick={handleUpdateProfile}
                      disabled={actionLoading}
                      className="px-6 py-2 bg-[#6B72FF] hover:bg-[#5a61db] disabled:bg-gray-600 text-white rounded-lg transition-all duration-200"
                    >
                      {actionLoading ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={() => {
                        setEditingProfile(false);
                        setNewFullName(profile?.full_name || '');
                        setError('');
                      }}
                      className="px-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-all duration-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-white text-lg">{profile?.full_name || 'Not set'}</p>
              )}
            </div>

            {/* Email Display (not editable here, moved to security) */}
            <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-6">
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">Email Address</h3>
                <p className="text-gray-400 text-sm mb-4">Your current email address</p>
                <p className="text-white text-lg">{profile?.email}</p>
              </div>
            </div>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            {/* Change Email */}
            <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">Email Address</h3>
                  <p className="text-gray-400 text-sm mt-1">Current: {profile?.email}</p>
                </div>
                {!changingEmail && (
                  <button
                    onClick={() => setChangingEmail(true)}
                    className="px-4 py-2 bg-[#6B72FF] hover:bg-[#5a61db] text-white rounded-lg transition-all duration-200"
                  >
                    Change Email
                  </button>
                )}
              </div>
              
              {changingEmail && (
                <div className="space-y-4">
                  <input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="Enter new email address"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6B72FF] transition-all duration-200"
                  />
                  <div className="flex gap-3">
                    <button
                      onClick={handleUpdateEmail}
                      disabled={actionLoading}
                      className="px-6 py-2 bg-[#6B72FF] hover:bg-[#5a61db] disabled:bg-gray-600 text-white rounded-lg transition-all duration-200"
                    >
                      {actionLoading ? 'Updating...' : 'Update Email'}
                    </button>
                    <button
                      onClick={() => {
                        setChangingEmail(false);
                        setNewEmail('');
                        setError('');
                      }}
                      className="px-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-all duration-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Change Password */}
            <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">Password</h3>
                  <p className="text-gray-400 text-sm mt-1">Update your password</p>
                </div>
                {!changingPassword && (
                  <button
                    onClick={() => setChangingPassword(true)}
                    className="px-4 py-2 bg-[#6B72FF] hover:bg-[#5a61db] text-white rounded-lg transition-all duration-200"
                  >
                    Change Password
                  </button>
                )}
              </div>
              
              {changingPassword && (
                <div className="space-y-4">
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Current password"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6B72FF] transition-all duration-200"
                  />
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="New password (min 6 characters)"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6B72FF] transition-all duration-200"
                  />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-[#6B72FF] transition-all duration-200"
                  />
                  <div className="flex gap-3">
                    <button
                      onClick={handleUpdatePassword}
                      disabled={actionLoading}
                      className="px-6 py-2 bg-[#6B72FF] hover:bg-[#5a61db] disabled:bg-gray-600 text-white rounded-lg transition-all duration-200"
                    >
                      {actionLoading ? 'Updating...' : 'Update Password'}
                    </button>
                    <button
                      onClick={() => {
                        setChangingPassword(false);
                        setCurrentPassword('');
                        setNewPassword('');
                        setConfirmPassword('');
                        setError('');
                      }}
                      className="px-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-all duration-200"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Danger Zone Tab */}
        {activeTab === 'danger' && (
          <div className="backdrop-blur-xl bg-red-500/10 border border-red-500/30 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-red-400 mb-2">Delete Account</h3>
                <p className="text-gray-300 mb-1">
                  Once you delete your account, there is no going back. Please be certain.
                </p>
                <p className="text-gray-400 text-sm mb-6">
                  This will permanently delete your account, all your saved graphs, and any other data associated with your account.
                </p>
                <button
                  onClick={handleDeleteAccount}
                  disabled={actionLoading}
                  className="px-6 py-3 bg-red-500 hover:bg-red-600 disabled:bg-gray-600 text-white font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-red-500/50"
                >
                  {actionLoading ? 'Deleting...' : 'Delete My Account'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default function ProtectedAccountPage() {
  return (
    <AuthGuard>
      <AccountPage />
    </AuthGuard>
  );
}
