# Interview questions

Hard questions a reviewer could ask about this portfolio. The questions were drafted with an
AI assistant. The answers are mine and are filled in by hand; an empty answer means I have not
written it yet.

## How I work

1. Which parts of this repository did you write yourself, which did a coding agent write, and how do you review an agent's change before it merges?

   _Answer:_

2. Pick one decision in this repository that an agent proposed and you rejected. Why?

   _Answer:_

## Multilingual safety rules

3. The mutation score was 0.97 while Urdu recall was 0.00. Explain in one minute why mutation testing could not see that gap.

   _Answer:_

4. False alerts rose from 4.9% to 14.8%. Who pays for a false alert, and how would you decide whether that trade was worth it?

   _Answer:_

5. You wrote both the rules and the test cases. What would an independent test set change, and how would you get one?

   _Answer:_

## Live model comparison

6. The largest model passed 120 of 120 at about thirty times the cost of the smallest. Which would you ship, and what would you measure first?

   _Answer:_

7. Your first run reported 68 of 120 because replies were cut off at 200 tokens. How did you find it, and what check now stops it happening again?

   _Answer:_

8. The scorer failed a reply that refused to promise a guaranteed refund. Why is a phrase ban a weak check, and what are the limits of the negation window you replaced it with?

   _Answer:_

9. Every case shares four intents. How would you build a set that is hard enough to separate two good models?

   _Answer:_

## Tool-using agent

10. How do you tell a wrong tool choice from a right choice with wrong arguments, and why does the difference matter?

    _Answer:_

11. The agent must call no other tool once it has raised an urgent case. How is that enforced: by the prompt, by the code, or both?

    _Answer:_

## PostgreSQL

12. The composite index took a query from 67 ms to 0.126 ms. What does that index cost on writes, and when would you not add it?

    _Answer:_

13. The month filter only improved from 160 ms to 35 ms. Why, and what would you try next?

    _Answer:_

14. Why does the webhook queue use `FOR UPDATE SKIP LOCKED`, and what happens to a job if a worker dies after the provider accepted delivery?

    _Answer:_

15. Four and eight workers were slower than one in your benchmark. Give two plausible reasons and how you would test each.

    _Answer:_

16. In the school access lab, why is admission a security-definer function instead of a direct table write?

    _Answer:_

## Quality gates

17. A gate proof first passed wrongly because weakened tests scored exactly 0.90 against a 0.90 bar. What did that teach you about thresholds?

    _Answer:_

18. Branch protection is a setting, not a file. What stops someone turning it off?

    _Answer:_

## Divia

19. Why do the rules run before the model, and what does the model still add?

    _Answer:_

20. Two reads of a meter photo must agree. What happens when they disagree, and what is the failure you are designing against?

    _Answer:_

21. Who approves a change to a clinical threshold, and how does the code make sure an unapproved change cannot ship?

    _Answer:_

22. What would have to be true before you let the model, not the rules, decide an urgent case?

    _Answer:_
