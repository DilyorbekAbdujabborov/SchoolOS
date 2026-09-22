import {
  Award,
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  Compass,
  FileText,
  Flame,
  GraduationCap,
  LayoutDashboard,
  School,
  Send,
  Settings,
  Trophy,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "../components/PageHeader";
import { useAuth } from "../lib/auth";
import type { Role } from "../types";

interface GuideSection {
  title: string;
  icon: LucideIcon;
  summary: string;
  points: string[];
}

const STUDENT_SECTIONS: GuideSection[] = [
  {
    title: "Boshqaruv paneli",
    icon: LayoutDashboard,
    summary: "Platformaga kirganda birinchi ochiladigan sahifa — bugungi holatingiz bir qarashda.",
    points: [
      "Yuqorida darajangiz, jami XP va kunlik faollik seriyangiz ko'rsatiladi.",
      "\"Sinf reytingi\" va \"Umumiy reyting\" kartalari sizning o'rningizni ko'rsatadi.",
      "\"Reyting yetakchisi\" — hozirda birinchi o'rindagi o'quvchi.",
      "\"Yaqin vazifalar\" — yaqinda topshirish kerak bo'lgan test va topshiriqlar, har birida qancha XP berilishi yozilgan.",
    ],
  },
  {
    title: "Testlar",
    icon: FileText,
    summary: "O'qituvchi e'lon qilgan testlarni shu yerdan ishlaysiz.",
    points: [
      "Faqat \"E'lon qilingan\" testlar ochiq bo'ladi — qoralamalar ko'rinmaydi.",
      "Har bir testni faqat bir marta topshirish mumkin — qayta urinib bo'lmaydi.",
      "Ballingiz avtomatik hisoblanadi: XP = (to'g'ri javoblar %) × testning maksimal XP'si.",
    ],
  },
  {
    title: "Topshiriqlar",
    icon: ClipboardList,
    summary: "Test bo'lmagan vazifalar — insho, amaliy ish, sport va boshqalar.",
    points: [
      "Javobingizni matn yoki fayl (masalan, daftar sahifasi rasmi) sifatida yuklashingiz mumkin.",
      "Topshiriqni o'qituvchi qo'lda baholaydi, natija va izoh keyin ko'rinadi.",
    ],
  },
  {
    title: "Reyting",
    icon: BarChart3,
    summary: "O'quvchilar va sinflar bo'yicha umumiy XP reytingi.",
    points: ["\"O'quvchilar\" va \"Sinflar\" bo'limlari orasida almashtirishingiz mumkin."],
  },
  {
    title: "Yutuqlar",
    icon: Award,
    summary: "Muayyan shartlarni bajarganda avtomatik ochiladigan nishonlar.",
    points: ["Masalan: birinchi test, 100% natija, ma'lum XP chegarasi yoki uzoq faollik seriyasi."],
  },
  {
    title: "Seriya",
    icon: Flame,
    summary: "Ketma-ket necha kun faol bo'lganingizni ko'rsatadi.",
    points: ["Har kuni kamida bitta test yoki topshiriq bajarsangiz, seriyangiz davom etadi."],
  },
  {
    title: "Bildirishnomalar",
    icon: Bell,
    summary: "Yangi test, baholangan topshiriq va boshqa e'lonlar shu yerda to'planadi.",
    points: ["Telegram botni ulasangiz, bildirishnomalar telefoningizga ham keladi (Profil bo'limida)."],
  },
];

const TEACHER_SECTIONS: GuideSection[] = [
  {
    title: "Boshqaruv paneli",
    icon: LayoutDashboard,
    summary: "Bugungi darslaringiz va so'nggi o'quvchi natijalari bir joyda.",
    points: ["Sinflaringiz, testlaringiz, topshiriqlaringiz va o'qilmagan xabarlar soni yuqorida ko'rinadi."],
  },
  {
    title: "Sinflarim",
    icon: Users,
    summary: "Siz sinf rahbari bo'lgan sinf alohida, faqat dars beradigan sinflaringiz pastda.",
    points: [
      "O'z sinfingiz kartasida bugungi davomat: kelgan, kechikkan va kelmaganlar soni + ismlari ko'rsatiladi.",
      "Bu ma'lumot boshqa o'qituvchi sizning sinfingizda davomat belgilashi bilan darhol yangilanadi.",
    ],
  },
  {
    title: "Darslarim",
    icon: BookOpen,
    summary: "Dars jadvalingiz bo'yicha rejalashtirilgan darslar ro'yxati.",
    points: [],
  },
  {
    title: "Davomat",
    icon: ClipboardCheck,
    summary: "Dars uchun davomatni shu yerdan belgilaysiz.",
    points: ["Har bir o'quvchiga: keldi, kechikdi, kelmadi yoki sababli belgisini qo'yasiz."],
  },
  {
    title: "Testlar",
    icon: FileText,
    summary: "O'quvchilaringiz uchun test yaratasiz.",
    points: [
      "Savollarni bittalab qo'shasiz, har birida to'g'ri variantni belgilaysiz.",
      "Diqqat: haftasiga 2 martadan kam o'tiladigan fan uchun testda ko'pi bilan 10 ta savol bo'lishi mumkin.",
      "Tayyor bo'lgach \"E'lon qilish\" tugmasi bilan o'quvchilarga ochasiz.",
    ],
  },
  {
    title: "Topshiriqlar",
    icon: ClipboardList,
    summary: "Test bo'lmagan vazifalar — insho, amaliy ish va hokazo yaratasiz.",
    points: ["O'quvchi yuborgan javoblarni qo'lda baholaysiz, ball XP'ga avtomatik aylantiriladi."],
  },
  {
    title: "Vazifalarim",
    icon: Send,
    summary: "Direktor tomonidan sizga yuborilgan ma'muriy vazifalar (yig'ilish, hisobot va h.k.).",
    points: ["Bajargach \"Bajarildi\" tugmasini bosasiz."],
  },
];

const DIRECTOR_SECTIONS: GuideSection[] = [
  {
    title: "Boshqaruv paneli",
    icon: LayoutDashboard,
    summary: "Maktab bo'yicha umumiy statistika: o'quvchilar, o'qituvchilar, sinflar, bugungi davomat.",
    points: [],
  },
  {
    title: "O'quvchilar / O'qituvchilar",
    icon: GraduationCap,
    summary: "Hisoblarni yaratish, tahrirlash va faollashtirish/o'chirish.",
    points: [],
  },
  {
    title: "Sinflar / Fanlar",
    icon: School,
    summary: "Sinflarga rahbar tayinlash, fanlar ro'yxatini boshqarish.",
    points: [],
  },
  {
    title: "Dars jadvali",
    icon: CalendarDays,
    summary: "Haftalik jadval shabloni — shundan haqiqiy darslar avtomatik yaratiladi.",
    points: [],
  },
  {
    title: "Davomat",
    icon: ClipboardCheck,
    summary: "Har qanday sinf va sana bo'yicha davomat holatini ko'rasiz.",
    points: [],
  },
  {
    title: "Vazifa berish",
    icon: Send,
    summary: "O'qituvchilarga ma'muriy vazifa (yig'ilish, hisobot va h.k.) yuborasiz.",
    points: ["Bitta o'qituvchiga yoki bir vaqtda hammasiga yuborish mumkin — kim bajarganini shu yerdan kuzatasiz."],
  },
  {
    title: "XP va reyting",
    icon: Trophy,
    summary: "Maktab bo'yicha eng faol o'quvchi va sinflarni ko'rasiz.",
    points: [],
  },
  {
    title: "Yutuqlar",
    icon: Award,
    summary: "O'quvchilar avtomatik qo'lga kiritadigan nishonlarni yaratasiz va sozlaysiz.",
    points: [],
  },
  {
    title: "Sozlamalar",
    icon: Settings,
    summary: "Maktab vaqti bo'yicha cheklovlar va boshqa umumiy sozlamalar.",
    points: [],
  },
];

const SECTIONS_BY_ROLE: Record<Role, GuideSection[]> = {
  STUDENT: STUDENT_SECTIONS,
  TEACHER: TEACHER_SECTIONS,
  DIRECTOR: DIRECTOR_SECTIONS,
};

export function GuidePage() {
  const { user } = useAuth();
  const sections = SECTIONS_BY_ROLE[user?.role ?? "STUDENT"];
  const [activeIndex, setActiveIndex] = useState(0);
  const active = sections[activeIndex];

  return (
    <div className="space-y-6">
      <PageHeader title="Qo'llanma" />

      <div className="rounded-2xl bg-brand-600 p-6 text-white">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/20">
            <Compass size={22} />
          </span>
          <div>
            <p className="text-lg font-bold">Platforma bo'yicha qo'llanma</p>
            <p className="text-sm text-white/80">
              Bu yerda har bir bo'lim nima uchun kerakligini bilib olasiz. Chapdagi ro'yxatdan bo'limni tanlang.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        <div className="space-y-1">
          {sections.map((section, index) => (
            <button
              key={section.title}
              onClick={() => setActiveIndex(index)}
              className={`flex w-full items-center gap-3 rounded-xl border border-transparent px-3 py-2.5 text-left text-sm font-medium transition-colors ${
                index === activeIndex
                  ? "bg-brand-600 text-white"
                  : "hover-glow text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  index === activeIndex
                    ? "bg-white/20"
                    : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                }`}
              >
                {index + 1}
              </span>
              {section.title}
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-4 flex items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
              <active.icon size={19} />
            </span>
            <div>
              <p className="text-lg font-bold text-slate-900 dark:text-slate-50">{active.title}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">{active.summary}</p>
            </div>
          </div>
          {active.points.length > 0 && (
            <ul className="space-y-2">
              {active.points.map((point) => (
                <li key={point} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-200">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                  {point}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
