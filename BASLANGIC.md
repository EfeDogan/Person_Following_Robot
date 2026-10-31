# Gazebo ile insan takip projesine başlangıç

Bu klasördeki örnekler Gazebo Harmonic üzerinde simülasyonun temelini öğrenmek içindir. Önce robotu elle hareket ettirin, sonra yürüyen insanı ekleyin ve son olarak takip kontrolcüsünü deneyin. Bunlar son deney videoları değildir; Jackal, insanın bakış açısından kamera, kayıt ve deney doğrulaması daha sonra eklenecek.

## Boş gri ekran ve insan rotası düzeltmesi

31 Ekim incelemesinde gri pencerenin asıl takılma noktası süreç örneklemesiyle bulundu: GUI ana iş parçacığı `SceneManagerPrivate::ActorTrajectoryAt` içinde kalıyordu. Gazebo Sim 8.15 sürümünün bu kod yolunda, `<loop>false</loop>` için eklenen son rota kaydı toplam süreyi sıfıra düşürebiliyor; zaman azaltma döngüsü sonlanmıyor. Önceki sunucu ve grafik günlüklerini kontrol etmek bu hatayı tek başına ortaya çıkarmamıştı.

`02_insan.sdf` içinde öğrenme rotası `<loop>true</loop>` olarak değiştirildi. Bu yüzden insan 33 saniyelik rotayı tekrarlar; yeni turda başlangıç konumuna döner. Takip kodu yine 33. saniyede robotu durdurur. Bu tekrar davranışı son deney videosu için kullanılacak bir tasarım kararı değildir; geçerli Gazebo sürümünde arayüzün kilitlenmesini önleyen alıştırma çözümüdür. Son deney kaydı rota sıfırlanmadan önce kesilmelidir.

Düzeltmeyi almak için açık başlatıcıyı Ctrl+C ile kapatıp aynı komutu yeniden çalıştırın; Gazebo'yu yeniden kurmak gerekmez.

## Önerilen başlatma yöntemi Tek terminal

İlk sorun giderme sırasında aynı anda bir `01_robot.sdf` sunucusu ve iki `02_insan.sdf` sunucusu çalıştığı görüldü. Bunlar aynı servis ve topic adlarını kullanabilir. Yalnızca pencereyi kapatmak ayrı terminalde çalışan fizik sunucusunu durdurmaz. Ayrıca macOS grafik günlüklerinde malzeme/shader hataları bulundu. Aşağıdaki başlatıcı, örnekleri tek tek açar ve Component Inspector gibi bu alıştırmada gerekmeyen arayüz eklentilerini yüklemez. Bu, görsel donmanın kesin nedeninin doğrulandığı anlamına gelmez.

Önce eski elle açılmış Gazebo terminal süreçlerini Ctrl+C ile kapatın. Sonra tek bir terminalde:

```bash
cd '/Users/efeemirhandogan/Documents/ChatGPT/Robotic Proje'
python3 scripts/baslat.py insan
```

Sunucu ve hafif arayüz birlikte açılır. Simülasyon otomatik başlar; Play düğmesine basmanız gerekmez. İnsan üç simülasyon saniyesinden sonra yürümeye başlar, 33. saniyede alıştırma rotası başa döner. Kamera insanı otomatik takip etmediği için insan zamanla görüntüden çıkabilir. Simülasyon zaman sayacı ilerliyorsa fizik sunucusu durmamıştır.

Kapatmak için aynı terminalde **Ctrl+C** kullanın. Başlatıcı kendi açtığı sunucuyu ve arayüzü birlikte kapatır. Aynı başlatıcıyla ikinci bir örnek açılmasını kilitle önler. Günlükler her çalıştırma için `logs` altında ayrı klasöre yazılır. Bu yöntemi aşağıdaki eski çok terminalli yöntemle aynı anda kullanmayın.

Robot sahnesi:

```bash
python3 scripts/baslat.py robot
```

Otomatik takip:

```bash
python3 scripts/baslat.py takip --distance 1.2
```

Başlatıcı ağ ayarlarını kendisi yapar ve eski süreçlerle iletişimi karıştırmamak için `hri_launcher` partition'ını kullanır. Bu yöntemle açılan robotu başka terminalden elle sürmek için komutta aynı partition gerekir:

```bash
GZ_IP=127.0.0.1 GZ_PARTITION=hri_launcher gz topic -t /model/hri_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.3}, angular: {z: 0}'
```

Durma komutu:

```bash
GZ_IP=127.0.0.1 GZ_PARTITION=hri_launcher gz topic -t /model/hri_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0}, angular: {z: 0}'
```

Bu Mac'te eski `ogre` grafik motoru da denendi; `RenderTextureMetalId is not supported` hatasıyla arayüz kapandı. Bu yüzden başlatıcı `ogre2` kullanır. Grafik tarafında sorun sürerse `--render-engine ogre` önerisini bu kurulumda uygulamayın; ilgili çalıştırmanın `arayuz.log` dosyasını inceleyin.

## Alternatif yöntem Ayrı sunucu ve arayüz terminalleri

Aşağıdaki alıştırmalar eski elle başlatma yöntemini de açıklar. Öncelikle yukarıdaki tek terminal yöntemini kullanın; iki yöntemi birlikte çalıştırmayın.

## Kontrol edilen kurulum

31 Ekim 2026 tarihinde bu Mac'te Apple Silicon, Homebrew Gazebo Harmonic ve Gazebo Sim 8.15.0 bulundu. `ros2` komutu PATH üzerinde bulunmadı. Fizik sunucusu, hız komutları, robot odometrisi ve takip alıştırması çalıştırıldı. GUI süreci render motorunu başlattı; pencerenin görüntüsü otomatik inceleme aracıyla doğrulanamadı. Görsel model, malzeme ve insan yönelimi birlikte ekranda kontrol edilmeli.

Gazebo'nun mevcut Homebrew Python bağlayıcıları bulundu. Eksik protobuf bağımlılığı yalnızca proje içindeki `.venv` ortamına kuruldu; genel Python kurulumu değiştirilmedi. Bu ortam bu Mac'e özeldir, başka bilgisayara kopyalanmamalıdır.

## Temel kavramlar

| Kavram | Bu projede karşılığı |
| --- | --- |
| World | Koridorun, robotun, insanın ve ışığın bulunduğu sahne |
| SDF | Sahneyi ve modelleri tarif eden XML dosyası |
| Model | Robot, duvar veya masa gibi bir nesne |
| Link | Robotun gövdesi veya tekerleği gibi tek bir katı parça |
| Joint | İki parçayı bağlayan eklem; tekerlek burada döner |
| Visual | Ekranda görünen şekil veya mesh |
| Collision | Fizik motorunun temas hesabında kullandığı şekil |
| Plugin | Tekerlekleri sürmek gibi davranış ekleyen bileşen |
| Topic | Konum veya hız komutu mesajlarının geçtiği adlandırılmış kanal |
| Actor | İskelet animasyonu ve zamanlanmış rotası olan insan modeli |

Robotun hareketi fizik motoruyla hesaplanır. İnsan actor'ü ise zamanlanmış animasyondur; kendiliğinden fiziksel çarpışma davranışı taşımaz. İnsanla çarpışmayı değerlendirmek için daha sonra ayrıca geometrik yakınlık/örtüşme kontrolü gerekir.

## Birinci alıştırma Robotu elle sürmek

Terminal uygulamasını açın. Her terminal penceresinde önce proje klasörüne gidin ve aynı yerel iletişim ayarlarını yükleyin. GUI, sunucu, hız komutları ve Python kontrolcüsü aynı ayarları kullanmalıdır:

```bash
cd '/Users/efeemirhandogan/Documents/ChatGPT/Robotic Proje'
source scripts/gazebo_env.sh
```

Bu dosya `GZ_IP=127.0.0.1` ve `GZ_PARTITION=hri_local` ayarlar. İletişim adresini bu Mac'e sabitleyerek ağ arayüzü seçimi sorunlarını azaltır. Sistem ağ ayarlarını değiştirmez; açılan her yeni terminalde yeniden yüklenmelidir. Başka bir bilgisayardaki Gazebo'ya bağlanmak için bu yerel adres uygun değildir. Yerel sunucu ve topic iletişimi bu ayarla yeniden test edildi; kullanıcının bildirdiği multicast hatası test sırasında tekrar üretilemedi.

Terminal 1, fizik sunucusu:

```bash
gz sim -s -r worlds/01_robot.sdf
```

Terminal 2, görsel arayüz:

```bash
gz sim -g
```

Mac'te sunucu ile arayüzü ayrı çalıştırıyoruz. `-s` fizik sunucusunu, `-g` arayüzü, `-r` simülasyonun hemen başlamasını ifade eder. Arayüzde iki uzun duvar arasında küçük mavi bir eğitim robotu görmelisiniz. Son deneyde Jackal modeline geçeceğiz.

Terminal 3, ileri gitme komutu:

```bash
gz topic -t /model/hri_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.3}, angular: {z: 0}'
```

`linear.x` ileri hızı metre/saniye, `angular.z` dönüş hızını radyan/saniye olarak belirtir. Bu tek komut kalıcı hareket başlatır; terminal komutunun bitmesi robotu durdurmaz.

Durma komutu:

```bash
gz topic -t /model/hri_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0}, angular: {z: 0}'
```

Yavaşça dönerek ilerleme:

```bash
gz topic -t /model/hri_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.2}, angular: {z: 0.25}'
```

Konum ve hız verisini izleme:

```bash
gz topic -e -t /model/hri_robot/odometry
```

Bu izlemeyi Ctrl+C ile kapatın. Sonra robotu sıfır hız komutuyla durdurun. Sonraki alıştırmadan önce sunucuyu Terminal 1'de Ctrl+C ile kapatın; eski GUI'yi de kapatıp yeniden açın. Aynı anda iki örnek sunucuyu çalıştırmayın, çünkü robot topic adları aynıdır.

## İkinci alıştırma Yürüyen insan

Terminal 1:

```bash
gz sim -s worlds/02_insan.sdf
```

Terminal 2:

```bash
gz sim -g
```

Arayüzde Play düğmesine basın. İnsan ilk üç simülasyon saniyesinde yerinde kalır, sonra koridor boyunca +X yönünde 30 metre yürür. 33. saniyede rota başa döner. Modelin bacak animasyonu bu bekleme sırasında da oynayabilir. Bu alıştırmada robot kendiliğinden takip etmez.

İnsan modeli Gazebo Fuel'den bu Mac'e indirildi. Başka bir makinede ilk açılış internet gerektirebilir. Önceden indirmek için:

```bash
gz fuel download -u 'https://fuel.gazebosim.org/1.0/Mingfei/models/actor'
```

Sahnedeki `<actor name="walking_person">` bölümü insanı tanımlar:

- `<skin>`: insanın görünümü.
- `<animation name="walk">`: yürüyüş iskelet animasyonu.
- `<script>`: otomatik başlama ve tekrar davranışı.
- `<waypoint>`: belirli bir simülasyon zamanında ulaşılacak poz.

`<pose>3 0 1 0 0 0</pose>` sırasıyla x, y, z, roll, pitch, yaw değerlerini içerir. Konum metre, açılar radyandır. İnsan meshinin ekseni ve yüksekliği modele özgüdür; model değişirse görsel kontrol gerekir. Dosyada bir saniyelik rota noktaları var; beklemeden yürümeye geçişte spline geçişi bulunur.

## Üçüncü alıştırma Otomatik takip

İkinci alıştırmanın sunucusunu ve GUI'sini kapatın. Aynı `02_insan.sdf` sahnesini yeniden açın fakat henüz Play'e basmayın.

Terminal 1:

```bash
gz sim -s worlds/02_insan.sdf
```

Terminal 2:

```bash
gz sim -g
```

Terminal 3:

```bash
.venv/bin/python scripts/takip.py --distance 1.2
```

Şimdi GUI'de Play'e basın. Kontrolcü robotun konumunu odometri kanalından alır, bilinen insan rotasından hedef konumu hesaplar ve tekerlek sürücüsüne hız komutları yollar. Başlangıçta robot yerini ayarlar; birkaç saniye sonra insanın hızına ve hedef boşluğa yaklaşır. Terminalde zaman, tahmini boşluk ve hız komutu görünür. 33. simülasyon saniyesinde takip biter ve sıfır hız komutu gönderilir. Kontrolcüyü Ctrl+C ile kapatmak da durma komutu gönderir.

0,6 m veya 2,0 m için her seferinde sahneyi sıfırdan başlatıp yalnızca son parametreyi değiştirin:

```bash
.venv/bin/python scripts/takip.py --distance 0.6
```

```bash
.venv/bin/python scripts/takip.py --distance 2.0
```

Robotun konumu geri beslemeli olarak ölçülür; insanınki ise bilinen düz yürüyüş rotasından tahmin edilir. Kod görüntüden insan tespit etmez. Yazdırılan boşluk, insan meshinin gerçek sırt yüzeyini veya yürüyüş salınımını ölçmez. Bu nedenle buradaki değerler proje raporunda doğrulanmış RMSE sonucu olarak kullanılmamalıdır. Rota düzenlenirse kontrolcüdeki rota hesabı da değişmelidir. Kontrolcüyü `01_robot.sdf` ile çalıştırmayın.

## Nasıl yeni model eklenir

Bu başlangıçta modelleri SDF dosyasına ekliyoruz; böylece sahneyi başkaları da aynı şekilde açabiliyor. Dış bir model için dünya içindeki `<world>` bölümüne `<include>` eklenir:

```xml
<include>
  <uri>MODELİN_GAZEBO_FUEL_URL_ADRESİ</uri>
  <name>benzersiz_model_adi</name>
  <pose>5 1 0 0 0 0</pose>
</include>
```

Yukarıdaki URI bir yer tutucudur; gerçek model adresiyle değiştirilmelidir. Modeli eklemek ona takip davranışı kazandırmaz. Tekerlekli robotun eklemleri ve DiffDrive gibi bir sürücü eklentisi de olmalıdır. Bu yüzden önce çalıştığı doğrulanmış eğitim robotuyla ilerliyoruz. Duvar ve zemin gibi basit nesneler bu örnekte doğrudan `<model>` ve kutu/düzlem geometrileriyle tanımlıdır; indirme gerektirmez.

## Ubuntu bilgisayara geçiş

Ubuntu sürümü henüz o bilgisayarda kontrol edilmedi. Önce orada şu çıktıları alın:

```bash
cat /etc/os-release
uname -m
gz sim --versions
which ros2
```

Ubuntu 26.04 için güncel varsayılan ROS/Gazebo eşleşmesi ROS 2 Lyrical ve Gazebo Jetty'dir. Ubuntu 24.04 için Jazzy ve Harmonic kullanılabilir. Ubuntu 26.10 farklıdır; 26.04 için verilen paket komutlarını ona doğrudan uygulamayın. Seçilen robot paketinin de seçilen ROS sürümünü desteklediği ayrıca kontrol edilmelidir.

World dosyaları taşınabilir, ancak buradaki Python kontrolcü `gz.transport13` ve `gz.msgs10` ile Harmonic'e özeldir. Jetty'nin bağlayıcı sürümleri farklı olabilir; importlar ve bağımlılıklar uyarlanıp yeniden denenmelidir. ROS aşamasında kontrolcüyü ROS 2 düğümüne taşıyıp `ros_gz` köprüsüyle Gazebo'ya bağlamak planlanıyor. Mac'teki `.venv` klasörünü Ubuntu'ya taşımayın.

Bu Mac'te ortamı yeniden oluşturmak gerekirse aşağıdaki komutlar kullanılabilir. Bunlar Ubuntu kurulum komutları değildir:

```bash
/opt/homebrew/bin/python3.14 -m venv --system-site-packages .venv
.venv/bin/python -m pip install 'protobuf>=7.36.2,<8'
```

## Öğrenme demosundan dönem projesine geçiş

1. Elle sürüşü ve topic/konum ilişkisini öğrenin.
2. Actor rotasını ve robot kontrolcüsünü anlayın.
3. Son deney için tek robot modelini seçin; Jackal'a geçişi ve paket uyumunu doğrulayın.
4. İnsan konumunu, robot ön kenarını ve insan sırtını aynı koordinat sisteminde tanımlayın; gerçek mesafe ölçümünü ekleyin.
5. İnsanın baş hizasında arka yöne bakan kamerayı ekleyin; video kaydını hazırlayın.
6. Başlangıç geçişlerini videodan çıkarın; tüm koşullarda aynı kayıt penceresini kullanın.
7. Üç mesafeyi teknik olarak doğrulayın, sonra 3–5 kişiyle pilot yapın.

## Sorun giderme

- `Exception sending a multicast message: Can't assign requested address` görülüyorsa: eski sunucu ve GUI'yi kapatın. Sunucu, GUI ve komut terminalinin her birinde `source scripts/gazebo_env.sh` çalıştırıp yeniden başlatın. Bu hata model dosyasından ayrı bir ağ iletişimi sorunudur. Devam ederse hata veren terminaldeki `env | rg '^GZ_(IP|PARTITION)='` çıktısını ve güncel ağ arayüzlerini kontrol edin.
- Dosyanın adı `01_robot.sdf`; `01_robot_.sdf` değildir.
- Sahne duruyorsa: Play düğmesini kontrol edin; `-r` verilmediyse başlangıçta duraklatılır.
- Robot komut almıyorsa: `gz topic -l` ile kanalları kontrol edin; diğer örnek sunucularını kapatın.
- İnsan görünmüyorsa: Fuel indirmesini ve interneti kontrol edin; GUI terminalindeki mesh hatalarını okuyun.
- Kamera boş bir yeri gösteriyorsa: robot başlangıçta x=0, insan x=3 konumundadır; entity listesinde ilgili modeli seçerek bulun.
- Python `gz` veya `google` import hatası veriyorsa: sistem Python'u yerine `.venv/bin/python` kullanın.
- Yeniden takip denemesinde robot yürüyen insanı bulamıyorsa: world'ü kapatıp yeniden açın; süre 33 saniyeyi geçince demo tamamlanır.
- GUI'deki malzeme uyarıları: insanın görünümünü ekranda kontrol edin; son deney için eksik doku veya malzemeleri düzeltmeden video üretmeyin.

## Kaynaklar

- Robot dünya dosyası, bu bilgisayardaki Gazebo Sim 8 `diff_drive.sdf` örneğinden ölçeklenerek uyarlandı: https://github.com/gazebosim/gz-sim/blob/gz-sim8/examples/worlds/diff_drive.sdf
- Robot hareketi: https://gazebosim.org/docs/harmonic/moving_robot/
- İnsan animasyonu ve actor davranışı: https://gazebosim.org/docs/harmonic/actors/
- Kullanılan insan modeli: https://fuel.gazebosim.org/1.0/Mingfei/models/actor
- ROS/Gazebo sürüm eşleşmeleri: https://gazebosim.org/docs/ionic/ros_installation/

Paylaşılacak son paket hazırlanırken dış modellerin lisans ve atıf koşullarını model metadata dosyalarından ayrıca kaydedin.
