"""Token counts per prompt for the four noise categories of run_dialect_stress_matrix.py.
Needs only the tokenizer files (no GPU, no model weights).
Run:  python3 -I checks/tokenizer_fragmentation.py /tmp/falcon-7b
"""
import sys
from statistics import mean

CATEGORIES = {
    "Arabizi with numerals (3,5,7)": [
        "kam el fayedah 3la el qard el shakhy? abi a3ref 7ag el tasdeed kam shahr?",
        "shoo el raseed el baqy fe 7sabi? 5aberny bser3ah",
        "qol lee kam sa3ah yfta7 el far3 el yom? 6alabtkm 3ashan a5alles",
        "plz kam el gharamah ely nazlah 3lay 3ashan el ta25eer?",
        "abi aswe tajdeed 7ag el ro5sah, kam ybeeli adfa3?",
        "3ndy so2al, kam yom ybeeleha el she7nah 7ata tow9al?",
    ],
    "Arabizi pure phonetic (no digits)": [
        "shouf lee kam el mablagh el matloob mini lil fatora?",
        "ebgha aref kam saer el tazkara lil rehlah?",
        "gool li kam saah yebghalha el moamalah?",
        "ya akhi kam raqm el talab hagi?",
        "kam had el seheb el yawmi min el atm?",
        "badi aaref adeysh lezem edfaa lal tasjil?",
    ],
    "Gulf phonetic spelling (Arabic script)": [
        "جول لي جم الحساب مالي اللي باقي بالبنك؟",
        "تشيف اقدر ادفع الرسوم؟ وجم يبيلها وقت؟",
        "جم غرامة التأخير اللي جالوها حق المخالفة؟",
        "ابي اعرف جم يوم اجازتي اللي باجية بالسيستم؟",
        "جم السعر مال الدخول؟ تراني ياي من بعيد",
        "تشوف لي جم رقم الغرفة اللي حجزوها حجي؟",
    ],
    "Orthographic chat slang (missing dots/hamza)": [
        "كم مده انتها الاقامه مالت العامله اللي عندى؟",
        "ابغي ادفع الفاتوره كم المبلغ الاجمالى بظبط؟",
        "ما هو رقم الحساب المصرفى مال الشركه فالبنك؟",
        "كم رسوم ارجاع الجواز من الاداره؟",
        "ابى اشوف كم نقطه عندى بالبطاقه؟",
        "كم يوم باقى على تجديد الملكيه حقت السياره؟",
    ],
}


def report(count_tokens):
    print(f"{'category':46} {'tokens/prompt':>13} {'chars/token':>12}")
    for cat, prompts in CATEGORIES.items():
        toks = [count_tokens(p) for p in prompts]
        cpt = [len(p) / t for p, t in zip(prompts, toks)]
        print(f"{cat:46} {mean(toks):13.1f} {mean(cpt):12.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: tokenizer_fragmentation.py <local tokenizer folder>")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(sys.argv[1], local_files_only=True)
    report(lambda s: len(tok.encode(s, add_special_tokens=False)))
