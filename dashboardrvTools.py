import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import seaborn as sns # type: ignore
import os
from datetime import datetime
import pdfkit # type: ignore

class RVToolsAnalyzer:
    def __init__(self, excel_path):
        """
        Inicializa el analizador de RVTools
        
        Args:
            excel_path (str): Ruta al archivo Excel de RVTools
        """
        self.excel_path = excel_path
        self.vms_df = None
        self.datastores_df = None
        self.hosts_df = None
        self.snapshots_df = None
        self.output_dir = 'rvtools_analysis_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Cargar los datos
        self.load_data()
    
    def load_data(self):
        """Carga los datos de las diferentes hojas del Excel"""
        print("Cargando datos de RVTools...")
        
        # Cargar las VMs (hoja vInfo)
        try:
            self.vms_df = pd.read_excel(self.excel_path, sheet_name='vInfo')
            self.vms_df.rename(columns={
                'Provisioned MiB': 'Provisioned MB',
                'In Use MiB': 'In Use MB',
                'Creation date': 'InstallDate'
            }, inplace=True)
            print(f"Datos de VMs cargados: {len(self.vms_df)} registros")
        except Exception as e:
            print(f"Error al cargar datos de VMs: {e}")
            self.vms_df = pd.DataFrame()
        
        # Cargar datastores (hoja vDatastore)
        try:
            self.datastores_df = pd.read_excel(self.excel_path, sheet_name='vDatastore')
            self.datastores_df.rename(columns={
                'Name': 'Datastore',
                'Capacity MiB': 'CapacityGB',
                'Free MiB': 'FreeGB'
            }, inplace=True)
            self.datastores_df['CapacityGB'] = self.datastores_df['CapacityGB'] / 1024
            self.datastores_df['FreeGB'] = self.datastores_df['FreeGB'] / 1024
            print(f"Datos de datastores cargados: {len(self.datastores_df)} registros")
        except Exception as e:
            print(f"Error al cargar datos de datastores: {e}")
            self.datastores_df = pd.DataFrame()
        
        # Cargar hosts (hoja vHost)
        try:
            self.hosts_df = pd.read_excel(self.excel_path, sheet_name='vHost')
            self.hosts_df.rename(columns={
                '# CPU': 'CPUs',
                '# Memory': 'Total Memory GB',
                'Memory usage %': 'Memory Usage Percent'
            }, inplace=True)
            self.hosts_df['Total Memory GB'] = self.hosts_df['Total Memory GB'] / 1024
            print(f"Datos de hosts cargados: {len(self.hosts_df)} registros")
        except Exception as e:
            print(f"Error al cargar datos de hosts: {e}")
            self.hosts_df = pd.DataFrame()
        
        # Cargar snapshots (hoja vSnapshot)
        try:
            self.snapshots_df = pd.read_excel(self.excel_path, sheet_name='vSnapshot')
            print(f"Datos de snapshots cargados: {len(self.snapshots_df)} registros")
        except Exception as e:
            print(f"Error al cargar datos de snapshots: {e}")
            self.snapshots_df = pd.DataFrame()
    
    def analyze_vm_power_state(self):
        """Analiza y grafica el estado de energía de las VMs"""
        if self.vms_df.empty:
            print("No hay datos de VMs para analizar")
            return
        
        print("Analizando estado de energía de VMs...")
        
        # Asegurarse de que la columna Powerstate existe
        if 'Powerstate' not in self.vms_df.columns:
            print("No se encontró la columna 'Powerstate' en los datos")
            return
        
        # Contar VMs por estado
        power_counts = self.vms_df['Powerstate'].value_counts()
        
        # Definir colores para los estados
        colors = ['green' if state == 'poweredOn' else 'red' if state == 'poweredOff' else 'gray' for state in power_counts.index]
        
        # Crear gráfico
        plt.figure(figsize=(10, 6))
        ax = power_counts.plot(kind='bar', color=colors)
        plt.title('Estado de Energía de Máquinas Virtuales', fontsize=15)
        plt.xlabel('Estado', fontsize=12)
        plt.ylabel('Cantidad de VMs', fontsize=12)
        plt.xticks(rotation=0)
        
        # Añadir etiquetas con valores
        for i, v in enumerate(power_counts):
            ax.text(i, v + 0.1, str(v), ha='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/vm_power_state.png')
        plt.close()
        
        print(f"Resumen de estados: {dict(power_counts)}")
        
        return power_counts
    
    def analyze_largest_vms(self, top_n=10):  # Cambiado de 5 a 10
        """
        Identifica y grafica las VMs más grandes en términos de CPU y RAM
        
        Args:
            top_n (int): Número de VMs a mostrar
        """
        if self.vms_df.empty:
            print("No hay datos de VMs para analizar")
            return
        
        print(f"Identificando las {top_n} VMs más grandes...")
        
        # Verificar columnas necesarias
        required_columns = ['VM', 'CPUs', 'Memory']
        for col in required_columns:
            if col not in self.vms_df.columns:
                print(f"No se encontró la columna '{col}' en los datos")
                return
        
        # Top VMs por CPU
        top_cpu_vms = self.vms_df.sort_values('CPUs', ascending=False).head(top_n)
        
        # Top VMs por RAM
        top_memory_vms = self.vms_df.sort_values('Memory', ascending=False).head(top_n)
        
        # Crear gráfico para CPUs
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x='VM', y='CPUs', data=top_cpu_vms, palette='viridis')
        plt.title(f'Top {top_n} VMs por CPU', fontsize=15)
        plt.xlabel('Máquina Virtual', fontsize=12)
        plt.ylabel('Número de CPUs', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Añadir etiquetas con valores
        for i, v in enumerate(top_cpu_vms['CPUs']):
            ax.text(i, v + 0.1, str(v), ha='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/top_cpu_vms.png')
        plt.close()
        
        # Crear gráfico para RAM
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x='VM', y='Memory', data=top_memory_vms, palette='viridis')
        plt.title(f'Top {top_n} VMs por Memoria RAM', fontsize=15)
        plt.xlabel('Máquina Virtual', fontsize=12)
        plt.ylabel('Memoria (MB)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Añadir etiquetas con valores
        for i, v in enumerate(top_memory_vms['Memory']):
            ax.text(i, v + 0.1, f"{v:.1f} Mb", ha='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/top_memory_vms.png')
        plt.close()
        
        print(f"Top {top_n} VMs por CPU: {', '.join(top_cpu_vms['VM'].tolist())}")
        print(f"Top {top_n} VMs por Memoria: {', '.join(top_memory_vms['VM'].tolist())}")
    
    def analyze_disk_usage(self, top_n=10):  # Cambiado de 5 a 10
        """
        Analiza y grafica las VMs con mayor uso de disco
        
        Args:
            top_n (int): Número de VMs a mostrar
        """
        if self.vms_df.empty:
            print("No hay datos de VMs para analizar")
            return
        
        print(f"Analizando uso de disco de las VMs...")
        
        # Verificar si existe la columna de tamaño de disco
        disk_column = None
        possible_columns = ['Provisioned MB', 'UsedMB', 'CapacityMB', 'In Use MB']
        
        for col in possible_columns:
            if col in self.vms_df.columns:
                disk_column = col
                break
        
        if not disk_column:
            print("No se encontró columna de uso de disco en los datos")
            return
        
        # Convertir a GB para mejor visualización
        self.vms_df['DiskGB'] = self.vms_df[disk_column] / 1024
        
        # Top VMs por uso de disco
        top_disk_vms = self.vms_df.sort_values('DiskGB', ascending=False).head(top_n)
        
        # Crear gráfico
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x='VM', y='DiskGB', data=top_disk_vms, palette='viridis')
        plt.title(f'Top {top_n} VMs por Uso de Disco', fontsize=15)
        plt.xlabel('Máquina Virtual', fontsize=12)
        plt.ylabel('Espacio en Disco (GB)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Añadir etiquetas con valores
        for i, v in enumerate(top_disk_vms['DiskGB']):
            ax.text(i, v + 0.1, f"{v:.1f} GB", ha='center', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/top_disk_vms.png')
        plt.close()
        
        print(f"Top {top_n} VMs por uso de disco: {', '.join(top_disk_vms['VM'].tolist())}")
    
    def analyze_datastores(self):
        """Analiza y grafica información de los datastores"""
        if self.datastores_df.empty:
            print("No hay datos de datastores para analizar")
            return
        
        print("Analizando datastores...")
        
        # Verificar columnas necesarias
        required_columns = ['Datastore', 'CapacityGB', 'FreeGB']
        for col in required_columns:
            if col not in self.datastores_df.columns:
                print(f"No se encontró la columna '{col}' en los datos de datastores")
                return
        
        # Calcular espacio usado
        self.datastores_df['UsedGB'] = self.datastores_df['CapacityGB'] - self.datastores_df['FreeGB']
        self.datastores_df['UsedPercent'] = (self.datastores_df['UsedGB'] / self.datastores_df['CapacityGB']) * 100
        
        # Ordenar por porcentaje de uso
        top_datastores = self.datastores_df.sort_values('UsedPercent', ascending=False)
        
        # Crear gráfico de barras apiladas
        plt.figure(figsize=(14, 8))
        
        # Limitar a 15 datastores para mejor visualización
        display_datastores = top_datastores.head(15)
        
        # Obtener 2 colores de la paleta viridis
        cmap = cm.get_cmap('viridis', 2)
        colors = [mcolors.to_hex(cmap(i)) for i in range(2)]

        # Crear gráfico de barras apiladas
        ax = display_datastores.plot(
            x='Datastore', 
            y=['UsedGB', 'FreeGB'],
            kind='bar',
            stacked=True,
            color=colors,
            figsize=(14, 8)
        )
        
        plt.title('Uso de Espacio en Datastores', fontsize=15)
        plt.xlabel('Datastore', fontsize=12)
        plt.ylabel('Espacio (GB)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(['Usado', 'Libre'])
        
        # Añadir etiquetas de porcentaje
        for i, v in enumerate(display_datastores['UsedPercent']):
            ax.text(i, 5, f"{v:.1f}%", ha='center', fontsize=9, color='black', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/datastore_usage.png')  # Guardar con el nombre requerido
        plt.close()
        
        print("Gráfico de uso de datastores guardado como 'datastore_usage.png'")
    
    def analyze_hosts(self):
        """
        Analiza y genera una tabla con información de los hosts.
        """
        if self.hosts_df.empty:
            print("No hay datos de hosts para analizar")
            return

        print("Analizando hosts...")

        # Verificar columnas necesarias
        required_columns = ['Host', 'Cores per CPU', 'Total Memory GB', 'Memory Usage Percent', 'Model', 'ESX Version']
        for col in required_columns:
            if col not in self.hosts_df.columns:
                print(f"No se encontró la columna '{col}' en los datos de hosts")
                return

        # Crear tabla con los datos relevantes
        hosts_table = self.hosts_df[['Host', 'Cores per CPU', 'Total Memory GB', 'Memory Usage Percent', 'Model', 'ESX Version']]
        print("Tabla de hosts generada:")
        print(hosts_table.head())

        # Guardar la tabla como archivo CSV para incluirla en el reporte
        output_path = f'{self.output_dir}/hosts_summary.csv'
        hosts_table.to_csv(output_path, index=False)
        print(f"Tabla de hosts guardada en: {output_path}")
    
    def project_growth(self):
        """
        Proyecta el crecimiento de recursos (CPU, RAM, disco) basado en el tiempo transcurrido
        desde la creación de las máquinas virtuales.
        """
        if self.vms_df.empty:
            print("No hay datos de VMs para proyectar crecimiento")
            return
        
        print("Proyectando crecimiento de recursos...")
        
        # Verificar columnas necesarias
        required_columns = ['VM', 'CPUs', 'Memory', 'Provisioned MB', 'InstallDate']
        for col in required_columns:
            if col not in self.vms_df.columns:
                print(f"No se encontró la columna '{col}' en los datos")
                return
        
        # Convertir la columna de fechas a formato datetime
        self.vms_df['InstallDate'] = pd.to_datetime(self.vms_df['InstallDate'], errors='coerce')
        
        # Calcular el tiempo transcurrido desde la instalación (en días)
        self.vms_df['DaysSinceInstall'] = (datetime.now() - self.vms_df['InstallDate']).dt.days
        
        # Filtrar VMs con datos válidos
        valid_vms = self.vms_df.dropna(subset=['DaysSinceInstall', 'CPUs', 'Memory', 'Provisioned MB'])
        
        # Calcular tasas de crecimiento por día
        valid_vms['CPU_GrowthRate'] = valid_vms['CPUs'] / valid_vms['DaysSinceInstall']
        valid_vms['Memory_GrowthRate'] = valid_vms['Memory'] / valid_vms['DaysSinceInstall']
        valid_vms['Disk_GrowthRate'] = (valid_vms['Provisioned MB'] / 1024) / valid_vms['DaysSinceInstall']  # Convertir MB a GB
        
        # Proyectar crecimiento a 1 año (365 días)
        valid_vms['Projected_CPUs'] = valid_vms['CPUs'] + (valid_vms['CPU_GrowthRate'] * 365)
        valid_vms['Projected_Memory'] = valid_vms['Memory'] + (valid_vms['Memory_GrowthRate'] * 365)
        valid_vms['Projected_Disk'] = (valid_vms['Provisioned MB'] / 1024) + (valid_vms['Disk_GrowthRate'] * 365)
        
        # Guardar proyección en un archivo CSV
        projection_file = f'{self.output_dir}/vm_growth_projection.csv'
        valid_vms[['VM', 'Projected_CPUs', 'Projected_Memory', 'Projected_Disk']].to_csv(projection_file, index=False)
        
        print(f"Proyección de crecimiento guardada en: {projection_file}")
    
    def identify_alerts(self):
        """Identifica posibles alertas en el entorno"""
        alerts = []
        snapshots_table_html = ""

        print("Buscando posibles alertas en el entorno...")

        # Alertas de VMs
        if not self.vms_df.empty:
            # VMs con 1 CPU (potencial cuello de botella)
            single_cpu_vms = self.vms_df[self.vms_df['CPUs'] == 1]
            if not single_cpu_vms.empty:
                alerts.append(f"VMs con 1 solo CPU: {len(single_cpu_vms)} VMs")
            
            # VMs con memoria baja (menos de 4 GB)
            if 'Memory' in self.vms_df.columns:
                low_mem_vms = self.vms_df[self.vms_df['Memory'] < 4]
                if not low_mem_vms.empty:
                    alerts.append(f"VMs con menos de 4GB de RAM: {len(low_mem_vms)} VMs")
        
        # Procesar snapshots desde la hoja vSnapshot
        if not self.snapshots_df.empty:
            vms_with_snapshots = self.snapshots_df[['VM', 'Name', 'Date / time']].copy()
            if not vms_with_snapshots.empty:
                alerts.append(f"VMs con snapshots activos: {len(vms_with_snapshots)} VMs")
                
                # Crear tabla de snapshots
                snapshots_table_html = vms_with_snapshots.to_html(index=False, classes='table table-striped')

        # Alertas de datastores
        if not self.datastores_df.empty:
            # Datastores con poco espacio libre
            if all(col in self.datastores_df.columns for col in ['CapacityGB', 'FreeGB']):
                self.datastores_df['UsedPercent'] = ((self.datastores_df['CapacityGB'] - self.datastores_df['FreeGB']) / 
                                                   self.datastores_df['CapacityGB']) * 100
                
                critical_datastores = self.datastores_df[self.datastores_df['UsedPercent'] > 90]
                if not critical_datastores.empty:
                    alerts.append(f"Datastores críticos (>90% llenos): {len(critical_datastores)} datastores")
                
                warning_datastores = self.datastores_df[(self.datastores_df['UsedPercent'] > 80) & 
                                                       (self.datastores_df['UsedPercent'] <= 90)]
                if not warning_datastores.empty:
                    alerts.append(f"Datastores en advertencia (80-90% llenos): {len(warning_datastores)} datastores")

        # Guardar alertas en un archivo
        with open(f'{self.output_dir}/alertas.txt', 'w') as f:
            f.write("ALERTAS DETECTADAS EN EL ENTORNO DE VIRTUALIZACIÓN\n")
            f.write("=" * 50 + "\n\n")
            
            if alerts:
                for i, alert in enumerate(alerts, 1):
                    f.write(f"{i}. {alert}\n")
            else:
                f.write("No se detectaron alertas significativas.\n")

        # Mostrar alertas en consola
        if alerts:
            print("\n¡ALERTAS DETECTADAS!")
            for alert in alerts:
                print(f" - {alert}")
        else:
            print("No se detectaron alertas significativas")
        
        return alerts, snapshots_table_html
    
    def analyze_powered_off_vms_disk_usage(self):
        """
        Analiza y grafica el uso de disco de las máquinas apagadas.
        """
        if self.vms_df.empty:
            print("No hay datos de VMs para analizar")
            return

        print("Analizando máquinas apagadas y su uso de disco...")

        # Filtrar máquinas apagadas
        powered_off_vms = self.vms_df[self.vms_df['Powerstate'] == 'poweredOff']

        if powered_off_vms.empty:
            print("No hay máquinas apagadas para analizar")
            return

        # Verificar si existe la columna de tamaño de disco
        if 'Provisioned MB' not in powered_off_vms.columns:
            print("No se encontró la columna 'Provisioned MB' en los datos")
            return

        # Convertir a GB para mejor visualización
        powered_off_vms = powered_off_vms.copy()  # Evitar SettingWithCopyWarning
        powered_off_vms['DiskGB'] = powered_off_vms['Provisioned MB'] / 1024

        # Ordenar por uso de disco en sentido descendente
        powered_off_vms = powered_off_vms.sort_values(by='DiskGB', ascending=False)

        # Crear gráfico
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='VM', y='DiskGB', data=powered_off_vms, palette=['red'] * len(powered_off_vms))
        plt.title('Uso de Disco de Máquinas Apagadas (Ordenado)', fontsize=15)
        plt.xlabel('Máquina Virtual', fontsize=12)
        plt.ylabel('Espacio en Disco (GB)', fontsize=12)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)

        # Añadir etiquetas con valores
        for i, v in enumerate(powered_off_vms['DiskGB']):
            ax.text(i, v + 0.1, f"{v:.1f} GB", ha='center', fontsize=8, rotation=90)

        # Calcular la sumatoria del almacenamiento
        total_disk_usage = powered_off_vms['DiskGB'].sum()

        # Añadir la sumatoria en la esquina superior derecha
        plt.text(
            0.95, 0.95,  # Coordenadas relativas (95% del ancho y alto del gráfico)
            f"Total Almacenamiento por recuperar: {total_disk_usage:.1f} GB",  # Texto a mostrar
            transform=plt.gca().transAxes,  # Transformación para usar coordenadas relativas
            fontsize=12, color='black', ha='right', va='top', bbox=dict(facecolor='white', alpha=0.8)
        )

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/powered_off_vms_disk_usage.png')
        plt.close()

        print("Gráfico de uso de disco de máquinas apagadas guardado como 'powered_off_vms_disk_usage.png'")
    
    def analyze_os_versions(self):
        """
        Analiza y grafica las versiones del sistema operativo según VMware Tools,
        diferenciando entre máquinas encendidas y apagadas.
        """
        if self.vms_df.empty:
            print("No hay datos de VMs para analizar")
            return

        print("Analizando versiones del sistema operativo...")

        # Verificar si existen las columnas necesarias
        if 'OS according to the VMware Tools' not in self.vms_df.columns or 'Powerstate' not in self.vms_df.columns:
            print("No se encontraron las columnas necesarias en los datos")
            return

        # Filtrar datos por estado de energía
        powered_on_vms = self.vms_df[self.vms_df['Powerstate'] == 'poweredOn']
        powered_off_vms = self.vms_df[self.vms_df['Powerstate'] == 'poweredOff']

        # Contar las versiones del sistema operativo para cada estado
        os_counts_on = powered_on_vms['OS according to the VMware Tools'].value_counts()
        os_counts_off = powered_off_vms['OS according to the VMware Tools'].value_counts()

        # Combinar los datos en un DataFrame
        os_counts_df = pd.DataFrame({
            'Encendidas': os_counts_on,
            'Apagadas': os_counts_off
        }).fillna(0)  # Rellenar NaN con 0

        # Ordenar por la suma de Encendidas y Apagadas
        os_counts_df['Total'] = os_counts_df['Encendidas'] + os_counts_df['Apagadas']
        os_counts_df = os_counts_df.sort_values(by='Total', ascending=False)

        # Crear gráfico apilado
        ax = os_counts_df[['Encendidas', 'Apagadas']].plot(kind='bar', stacked=True, figsize=(12, 6), color=['green', 'red'])
        plt.title('Distribución de Versiones del Sistema Operativo (Encendidas vs Apagadas)', fontsize=15)
        plt.xlabel('Versión del Sistema Operativo', fontsize=12)
        plt.ylabel('Cantidad de VMs', fontsize=12)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)
        plt.legend(title='Estado', loc='upper right', fontsize=10)

        # Añadir totales por sistema operativo encima de las columnas
        for i, (os, row) in enumerate(os_counts_df.iterrows()):
            total = row['Encendidas'] + row['Apagadas']
            ax.text(i, total + 0.5, f"{int(total)}", ha='center', fontsize=10, fontweight='bold', color='black')

        # Añadir etiquetas dentro de las columnas
        for i, (os, row) in enumerate(os_counts_df.iterrows()):
            if row['Encendidas'] > 0:
                ax.text(i, row['Encendidas'] / 2, f"{int(row['Encendidas'])}", ha='center', fontsize=9, color='white')
            if row['Apagadas'] > 0:
                ax.text(i, row['Encendidas'] + (row['Apagadas'] / 2), f"{int(row['Apagadas'])}", ha='center', fontsize=9, color='white')

        # Guardar el gráfico
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/os_versions.png')
        plt.close()

        print("Gráfico de versiones del sistema operativo guardado como 'os_versions.png'")
    
    def generate_report(self):
        """Genera un reporte completo con todos los análisis"""
        print("\nGenerando reporte completo...")

        # Ejecutar todos los análisis
        self.analyze_vm_power_state()
        self.analyze_largest_vms()
        self.analyze_disk_usage()
        self.analyze_datastores()
        self.analyze_hosts()
        self.analyze_powered_off_vms_disk_usage()
        self.analyze_os_versions()
        alerts, snapshots_table_html = self.identify_alerts()

        # Cargar alertas desde el archivo
        alerts_text = ""
        try:
            with open(f'{self.output_dir}/alertas.txt', 'r') as f:
                alerts_text = f.read()
        except:
            alerts_text = "No se pudieron cargar las alertas."

        # Cargar tabla de hosts
        hosts_table_html = ""
        try:
            hosts_table = pd.read_csv(f'{self.output_dir}/hosts_summary.csv')
            hosts_table_html = hosts_table.to_html(index=False, classes='table table-striped')
        except:
            hosts_table_html = "<p>No se pudo cargar la tabla de hosts.</p>"

        # Generar un informe HTML
        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>Análisis de RVTools - Reporte</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; text-align: center; }}
                h2 {{ color: #3498db; margin-top: 30px; }}
                img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0; }}
                .alert {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; 
                         padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .section {{ margin-bottom: 30px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 5px; }}
                .summary {{ background-color: #e0f7fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                pre {{ white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Análisis de Entorno de Virtualización - RVTools</h1>
            <p>Reporte generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Resumen de Hosts</h2>
                {hosts_table_html}
            </div>
            
            <div class="section">
                <h2>Estado de Energía de VMs</h2>
                <img src="vm_power_state.png" alt="Estado de VMs">
            </div>
            
            <div class="section">
                <h2>VMs más Grandes (CPU)</h2>
                <img src="top_cpu_vms.png" alt="Top VMs por CPU">
            </div>
            
            <div class="section">
                <h2>VMs más Grandes (Memoria)</h2>
                <img src="top_memory_vms.png" alt="Top VMs por Memoria">
            </div>
            
            <div class="section">
                <h2>VMs con Mayor Uso de Disco</h2>
                <img src="top_disk_vms.png" alt="Top VMs por Disco">
            </div>
            
            <div class="section">
                <h2>Uso de Datastores</h2>
                <img src="datastore_usage.png" alt="Uso de Datastores">
            </div>
            
            <div class="section">
                <h2>Máquinas Apagadas y Uso de Disco</h2>
                <img src="powered_off_vms_disk_usage.png" alt="Uso de Disco de Máquinas Apagadas">
            </div>
            
            <div class="section">
                <h2>Distribución de Versiones del Sistema Operativo</h2>
                <img src="os_versions.png" alt="Distribución de Versiones del Sistema Operativo">
            </div>
            
            <div class="section">
                <h2>Alertas Detectadas</h2>
                <pre>{alerts_text}</pre>
            </div>

            <div class="section">
                <h2>VMs con Snapshots Activos</h2>
                {snapshots_table_html}
            </div>
        </body>
        </html>"""

        # Guardar el informe HTML
        html_file = f'{self.output_dir}/reporte.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n¡Reporte HTML generado con éxito!")
        print(f"Los resultados están disponibles en: {os.path.abspath(html_file)}")

        # Convertir el HTML a PDF
        pdf_file = f'{self.output_dir}/reporte.pdf'
        try:
            pdfkit.from_file(html_file, pdf_file)
            print(f"¡Reporte PDF generado con éxito en: {os.path.abspath(pdf_file)}")
        except Exception as e:
            print(f"Error al generar el PDF: {e}")


# Ejemplo de uso
if __name__ == "__main__":
    # Solicitar al usuario la ruta del archivo RVTools
    print("=" * 50)
    print("ANALIZADOR DE RVTOOLS - ENTORNO DE VIRTUALIZACIÓN")
    print("=" * 50)
    
    rvtools_path = input("\nIntroduce la ruta completa al archivo Excel de RVTools: ")
    
    if not os.path.exists(rvtools_path):
        print(f"Error: El archivo {rvtools_path} no existe.")
    else:
        # Crear y ejecutar el analizador
        analyzer = RVToolsAnalyzer(rvtools_path)
        analyzer.generate_report()