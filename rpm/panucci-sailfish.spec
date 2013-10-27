Name: panucci
Version: 
Release: 1
Summary: Panucci - audiobook and podcast player

#Group:
License: GPLv3
URL: http://gpodder.org/panucci
Source:	panucci-%{version}.tar.gz
#BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires: python
Requires: gst-plugins-base, mutagen, pyqt, python-gstreamer

%description
An audiobook and podcast player written in python.

%prep
%setup -q


%build


%install
rm -rf $RPM_BUILD_ROOT
python device.py Sailfish
python setup.py install --root=$RPM_BUILD_ROOT
# Remove unneeded stuff
rm -r $RPM_BUILD_ROOT/usr/share/panucci/qml
rm -r $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/panucci/qtui
rm -r $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/panucci/gtk3ui
rm -r $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/panucci/gtkui
rm -r $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/panucci/qmlui


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_bindir}/*
%{_libdir}/*
%{_datadir}/*


%doc


%changelog
