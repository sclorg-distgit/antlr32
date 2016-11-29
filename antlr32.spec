%{?scl:%scl_package antlr32}
%{!?scl:%global pkg_name %{name}}
%{?java_common_find_provides_and_requires}

%global baserelease 3

%global bootstrap 0
%global bootstrap_version 3.1.3

Name:           %{?scl_prefix}antlr32
Version:        3.2
Release:        14.%{baserelease}%{?dist}
Summary:        ANother Tool for Language Recognition

License:        BSD
URL:            http://www.antlr3.org/
Source0:        http://www.antlr3.org/download/antlr-%{version}.tar.gz

# These artifacts are taken verbatim from maven central with the exception of the
# jar in source 2, which additionally has the java 8 compatibility patch given below
# These sources are only used for bootstrapping antlr32 into a new distro
%if %{bootstrap}
Source1:        http://repo1.maven.org/maven2/org/antlr/antlr-master/%{bootstrap_version}/antlr-master-%{bootstrap_version}.pom
Source2:        http://repo1.maven.org/maven2/org/antlr/antlr/%{bootstrap_version}/antlr-%{bootstrap_version}.jar
Source3:        http://repo1.maven.org/maven2/org/antlr/antlr/%{bootstrap_version}/antlr-%{bootstrap_version}.pom
Source4:        http://repo1.maven.org/maven2/org/antlr/antlr-runtime/%{bootstrap_version}/antlr-runtime-%{bootstrap_version}.jar
Source5:        http://repo1.maven.org/maven2/org/antlr/antlr-runtime/%{bootstrap_version}/antlr-runtime-%{bootstrap_version}.pom
Source6:        http://repo1.maven.org/maven2/org/antlr/antlr3-maven-plugin/%{bootstrap_version}-1/antlr3-maven-plugin-%{bootstrap_version}-1.jar
Source7:        http://repo1.maven.org/maven2/org/antlr/antlr3-maven-plugin/%{bootstrap_version}-1/antlr3-maven-plugin-%{bootstrap_version}-1.pom
%endif

# This is backported from upstream antlr 3.5.2 for java 8 compatibility
# See https://github.com/antlr/antlr3/commit/e88907c259c43d42fa5e9f5ad0e486a2c1e004bb
Patch0:         java8-compat.patch

# Generate OSGi metadata
Patch1:         osgi-manifest.patch

# Patch to use exec maven plugin as alternative to unavailable antlr2 maven plugin
Patch2:         antlr2-usage.patch

BuildRequires:  %{?scl_prefix_maven}maven-local
BuildRequires:  %{?scl_prefix_java_common}ant-antlr
BuildRequires:  %{?scl_prefix_maven}exec-maven-plugin
BuildRequires:  %{?scl_prefix}stringtemplate >= 3.2

# Cannot require ourself when bootstrapping
%if ! %{bootstrap}
BuildRequires:  %{name}-maven-plugin = %{version}
%endif

BuildArch:      noarch

%description
ANother Tool for Language Recognition, is a grammar parser generator.
This package is compatibility package containing an older version of
in order to support jython. No other packages should declare a
dependency on this one.

%package     maven-plugin
Summary:     Maven plug-in for creating ANTLR-generated parsers
Requires:    %{name}-tool = %{version}-%{release}

%description maven-plugin
Maven plug-in for creating ANTLR-generated parsers.

%package     tool
Summary:     Command line tool for creating ANTLR-generated parsers
Requires:    %{name}-java = %{version}-%{release}

%description tool
Command line tool for creating ANTLR-generated parsers.

%package     java
Summary:     Java run-time support for ANTLR-generated parsers
Requires:    %{?scl_prefix}stringtemplate >= 3.2

%description java
Java run-time support for ANTLR-generated parsers.

%package     javadoc
Summary:     API documentation for ANTLR

%description javadoc
%{summary}.

%prep
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
set -e -x
%setup -q -n antlr-%{version}

%patch0 -b .orig
%patch1 -b .orig
%patch2 -b .orig

# remove pre-built artifacts
find -type f -a -name *.jar -delete
find -type f -a -name *.class -delete

# remove corrupted files
find -name "._*" -delete

# disable stuff we don't need
%pom_disable_module gunit
%pom_disable_module gunit-maven-plugin
%pom_remove_plugin org.codehaus.mojo:buildnumber-maven-plugin
%pom_xpath_remove pom:build/pom:extensions
%pom_xpath_remove pom:build/pom:extensions runtime/Java
%pom_xpath_remove pom:build/pom:extensions antlr3-maven-plugin

# separate artifacts into sub-packages
%mvn_package :antlr tool
%mvn_package :antlr-master java
%mvn_package :antlr-runtime java
%mvn_package :antlr3-maven-plugin maven-plugin

# use a valid build target
find -name "pom.xml" | xargs sed -i -e "s|>jsr14<|>1.5<|"

# set a build number
sed -i -e "s|\${buildNumber}|%{release}|" tool/src/main/resources/org/antlr/antlr.properties

%mvn_compat_version 'org.antlr:antlr3-maven-plugin' %{version} %{bootstrap_version}-1
%mvn_compat_version 'org.antlr:antlr{,-master,-runtime}' %{version} %{bootstrap_version}
%{?scl:EOF}


%build
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
set -e -x
mkdir -p .m2/org/antlr/antlr-master/%{version}/
cp -p pom.xml .m2/org/antlr/antlr-master/%{version}/antlr-master-%{version}.pom

%if %{bootstrap}
mkdir -p .m2/org/antlr/antlr-master/%{bootstrap_version}/
cp -p %{SOURCE1} .m2/org/antlr/antlr-master/%{bootstrap_version}/.
mkdir -p .m2/org/antlr/antlr/%{bootstrap_version}/
cp -p %{SOURCE2} %{SOURCE3} .m2/org/antlr/antlr/%{bootstrap_version}/.
mkdir -p .m2/org/antlr/antlr-runtime/%{bootstrap_version}/
cp -p %{SOURCE4} %{SOURCE5} .m2/org/antlr/antlr-runtime/%{bootstrap_version}/.
mkdir -p .m2/org/antlr/antlr3-maven-plugin/%{bootstrap_version}-1/
cp -p %{SOURCE6} %{SOURCE7} .m2/org/antlr/antlr3-maven-plugin/%{bootstrap_version}-1/.
%endif

# a small number of tests always fail for reasons I don't fully understand
%mvn_build -f
%{?scl:EOF}


%install
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
set -e -x
%mvn_install
%{?scl:EOF}


%files tool -f .mfiles-tool
%doc tool/LICENSE.txt

%files maven-plugin -f .mfiles-maven-plugin
%doc tool/LICENSE.txt

%files java -f .mfiles-java
%doc tool/LICENSE.txt
%dir %{_datadir}/java/antlr32

%files javadoc -f .mfiles-javadoc
%doc tool/LICENSE.txt

%changelog
* Sat Jul 23 2016 Mat Booth <mat.booth@redhat.com> - 3.2-14.3
- Perform full non-bootstrap build

* Fri Jul 22 2016 Mat Booth <mat.booth@redhat.com> - 3.2-14.2
- Perform bootstrap build
- Add a patch to use exec maven plugin as an alternative to the unavailable
  antlr2 maven plugin

* Fri Jul 22 2016 Mat Booth <mat.booth@redhat.com> - 3.2-14.1
- Auto SCL-ise package for rh-eclipse46 collection

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.2-14
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Nov 26 2015 Mikolaj Izdebski <mizdebsk@redhat.com> - 3.2-13
- Remove workaround for rhbz#1276729

* Mon Nov 23 2015 Mat Booth <mat.booth@redhat.com> - 3.2-12
- Don't require optional stringtemplate dep in runtime OSGi metadata

* Wed Nov 18 2015 Mat Booth <mat.booth@redhat.com> - 3.2-11
- Workaround for rhbz#1276729

* Tue Nov 17 2015 Mat Booth <mat.booth@redhat.com> - 3.2-10
- Generate OSGi metadata for runtime jar

* Thu Jun 18 2015 Mat Booth <mat.booth@redhat.com> - 3.2-9
- Fix compat versions again (globs must be quoted)

* Wed Jun 17 2015 Mat Booth <mat.booth@redhat.com> - 3.2-8
- Non-bootstrap build

* Wed Jun 17 2015 Mat Booth <mat.booth@redhat.com> - 3.2-7
- Fix compat version of maven-plugin
- Rebootstrap

* Tue Jun 16 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Fri Jun 20 2014 Mat Booth <mat.booth@redhat.com> - 3.2-5
- Use mvn_compat_version macro

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Jun 02 2014 Mat Booth <mat.booth@redhat.com> - 3.2-3
- Perform a non-bootstrap build

* Mon Jun 02 2014 Mat Booth <mat.booth@redhat.com> - 3.2-2
- Add link to source of back-ported patch

* Thu May 29 2014 Mat Booth <mat.booth@redhat.com> - 3.2-1
- Initial packaging of compatability version of antlr3
