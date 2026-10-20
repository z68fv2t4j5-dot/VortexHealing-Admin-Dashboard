import React, { useState, useMemo } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';
import { Search, X } from 'lucide-react';
import '../styles/Pages.css';

export default function GlobalStudents() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedContact, setSelectedContact] = useState<any>(null);
  const [sortBy, setSortBy] = useState('name');
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);

  const { data: globalContacts = [], isLoading } = useQuery('globalStudents', () =>
    axios.get(`/api/global-students`).then(r => r.data).catch(() => [])
  );

  // Extract unique values for filters - countries only
  const allCountries = useMemo(() => {
    const countries = new Set<string>();
    globalContacts.forEach((c: any) => {
      if (c.country && c.country.trim()) {
        // Keep only real country names and Z-Deceased
        // Filter out Z-Unsubs, Z-moved, etc (except Z-Deceased)
        if (c.country === 'Z-Deceased' || !c.country.startsWith('Z-')) {
          countries.add(c.country);
        }
      }
    });
    return Array.from(countries).sort();
  }, [globalContacts]);

  // Filter and sort contacts
  const filteredContacts = useMemo(() => {
    let result = globalContacts.filter((contact: any) => {
      const matchesSearch = searchTerm === '' || (() => {
        const search = searchTerm.toLowerCase();
        // Search main fields
        if (
          contact.first_name?.toLowerCase().includes(search) ||
          contact.last_name?.toLowerCase().includes(search) ||
          contact.email?.toLowerCase().includes(search) ||
          contact.address_1?.toLowerCase().includes(search) ||
          contact.address_2?.toLowerCase().includes(search) ||
          contact.city?.toLowerCase().includes(search) ||
          contact.state?.toLowerCase().includes(search) ||
          contact.zip_code?.toLowerCase().includes(search) ||
          contact.country?.toLowerCase().includes(search) ||
          contact.notes?.toLowerCase().includes(search)
        ) return true;

        // Search all_data fields (classes and other columns)
        if (contact.all_data && typeof contact.all_data === 'object') {
          return Object.values(contact.all_data).some((value: any) =>
            String(value).toLowerCase().includes(search)
          );
        }
        return false;
      })();

      const matchesCountries = selectedCountries.length === 0 || selectedCountries.includes(contact.country);

      return matchesSearch && matchesCountries;
    });

    result.sort((a: any, b: any) => {
      switch(sortBy) {
        case 'name':
          return `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`);
        case 'email':
          return a.email.localeCompare(b.email);
        case 'city':
          return (a.city || '').localeCompare(b.city || '');
        case 'country':
          return (a.country || '').localeCompare(b.country || '');
        case 'state':
          return (a.state || '').localeCompare(b.state || '');
        case 'zip':
          return (a.zip_code || '').localeCompare(b.zip_code || '');
        default:
          return 0;
      }
    });

    return result;
  }, [globalContacts, searchTerm, sortBy, selectedCountries]);

  return (
    <div className="page">
      <div style={{ marginBottom: '2rem' }}>
        <h1>Global Students</h1>
        <p style={{ color: '#666' }}>
          {filteredContacts.length} contact{filteredContacts.length !== 1 ? 's' : ''} found
          {isLoading && ' • Loading...'}
          {!isLoading && globalContacts.length === 0 && ' • No contacts loaded'}
        </p>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#999' }}>
          Loading global contacts...
        </div>
      ) : globalContacts.length === 0 ? (
        <div style={{
          background: 'white',
          padding: '3rem',
          textAlign: 'center',
          borderRadius: '8px',
          color: '#999',
          border: '2px dashed #ddd'
        }}>
          <p style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>📁 No Global Contacts data</p>
          <p>Add CSV files to: <br /><code style={{ background: '#f0f0f0', padding: '0.5rem 1rem', borderRadius: '4px', fontSize: '0.9rem' }}>/Users/djw/Documents/VortexHealing Assistant Docs/All Global Contacts/</code></p>
          <p style={{ fontSize: '0.9rem', marginTop: '1rem' }}>Once files are added, refresh to load them.</p>
        </div>
      ) : (
        <>
          {/* Search and Filters */}
          <div style={{
            background: 'white',
            padding: '1.5rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'end', marginBottom: '1rem' }}>
              <div style={{ position: 'relative' }}>
                <Search size={18} style={{ position: 'absolute', left: '0.75rem', top: '0.75rem', color: '#999' }} />
                <input
                  type="text"
                  placeholder="Search all columns..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem 0.75rem 0.75rem 2.5rem',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '1rem'
                  }}
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    style={{
                      position: 'absolute',
                      right: '0.75rem',
                      top: '0.75rem',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: '#999'
                    }}
                  >
                    <X size={18} />
                  </button>
                )}
              </div>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                <option value="name">Sort: Name</option>
                <option value="email">Sort: Email</option>
                <option value="city">Sort: City</option>
                <option value="country">Sort: Country</option>
                <option value="state">Sort: State</option>
                <option value="zip">Sort: Zip Code</option>
              </select>
            </div>

            {/* Country Filter */}
            {allCountries.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.9rem', color: '#666' }}>
                  Countries:
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {allCountries.map(country => (
                    <button
                      key={country}
                      onClick={() => setSelectedCountries(prev =>
                        prev.includes(country) ? prev.filter(c => c !== country) : [...prev, country]
                      )}
                      style={{
                        padding: '0.5rem 0.75rem',
                        background: selectedCountries.includes(country) ? '#667eea' : '#f0f0f0',
                        color: selectedCountries.includes(country) ? 'white' : '#333',
                        border: 'none',
                        borderRadius: '20px',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        transition: 'all 0.2s'
                      }}
                    >
                      {country}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {selectedCountries.length > 0 && (
              <button
                onClick={() => { setSelectedCountries([]); }}
                style={{
                  padding: '0.5rem 1rem',
                  background: '#ff4757',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                Clear All Filters
              </button>
            )}
          </div>

          {/* Contacts Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
            {filteredContacts.map((contact: any, idx: number) => (
              <div
                key={idx}
                onClick={() => setSelectedContact(contact)}
                style={{
                  background: 'white',
                  padding: '1.5rem',
                  borderRadius: '8px',
                  border: '1px solid #e0e0e0',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                }}
              >
                <h3 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>
                  {contact.first_name} {contact.last_name}
                </h3>
                <p style={{ margin: '0 0 0.75rem 0', color: '#667eea', fontSize: '0.9rem' }}>
                  {contact.email}
                </p>
                <div style={{ display: 'grid', gap: '0.25rem', fontSize: '0.85rem', color: '#666' }}>
                  {contact.phone && <p style={{ margin: 0 }}>📱 {contact.phone}</p>}
                  {contact.city && <p style={{ margin: 0 }}>📍 {contact.city}, {contact.state || contact.country}</p>}
                  {contact.year_last && <p style={{ margin: 0 }}>📅 Last active: {contact.year_last}</p>}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Detail Modal */}
      {selectedContact && (
        <div
          onClick={() => setSelectedContact(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '2rem',
              maxWidth: '500px',
              width: '90%',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>
                {selectedContact.first_name} {selectedContact.last_name}
              </h2>
              <button
                onClick={() => setSelectedContact(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  color: '#999'
                }}
              >
                ×
              </button>
            </div>

            <div style={{ display: 'grid', gap: '1rem', maxHeight: '70vh', overflowY: 'auto' }}>
              {/* Contact Info */}
              {selectedContact.first_name && (
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Name</label>
                  <p style={{ margin: 0, color: '#333' }}>{selectedContact.first_name} {selectedContact.last_name}</p>
                </div>
              )}
              {selectedContact.email && (
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Email</label>
                  <p style={{ margin: 0, color: '#333' }}>{selectedContact.email}</p>
                </div>
              )}
              {selectedContact.address_1 && (
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Address</label>
                  <p style={{ margin: 0, color: '#333' }}>
                    {selectedContact.address_1}
                    {selectedContact.address_2 && `, ${selectedContact.address_2}`}
                  </p>
                </div>
              )}
              {(selectedContact.city || selectedContact.state || selectedContact.zip_code) && (
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Location</label>
                  <p style={{ margin: 0, color: '#333' }}>
                    {selectedContact.city && `${selectedContact.city}, `}
                    {selectedContact.state && `${selectedContact.state} `}
                    {selectedContact.zip_code && selectedContact.zip_code}
                  </p>
                </div>
              )}
              {selectedContact.country && (
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Country</label>
                  <p style={{ margin: 0, color: '#333' }}>{selectedContact.country}</p>
                </div>
              )}
              {selectedContact.notes && (
                <div>
                  <label style={{ display: 'block', fontWeight: 'bold', color: '#667eea', marginBottom: '0.25rem' }}>Notes</label>
                  <p style={{ margin: 0, color: '#333', wordBreak: 'break-word' }}>{selectedContact.notes}</p>
                </div>
              )}

              {/* Classes/Courses from all_data */}
              {selectedContact.all_data && Object.keys(selectedContact.all_data).length > 0 && (
                <>
                  <hr style={{ margin: '1rem 0', borderColor: '#ddd' }} />
                  <h3 style={{ color: '#667eea', marginTop: '1rem' }}>Classes & Courses</h3>
                  {Object.entries(selectedContact.all_data).map(([key, value]: [string, any]) => (
                    String(value).trim() && (
                      <div key={key}>
                        <label style={{ display: 'block', fontWeight: 'bold', color: '#764ba2', marginBottom: '0.25rem', fontSize: '0.9rem', textTransform: 'capitalize' }}>
                          {key.replace(/_/g, ' ')}
                        </label>
                        <p style={{ margin: 0, color: '#333', fontSize: '0.85rem' }}>
                          {String(value)}
                        </p>
                      </div>
                    )
                  ))}
                </>
              )}
            </div>

            <button
              onClick={() => setSelectedContact(null)}
              style={{
                marginTop: '1.5rem',
                width: '100%',
                padding: '0.75rem',
                background: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
