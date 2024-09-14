import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Column, CreateDateColumn, JoinColumn, ManyToOne, PrimaryColumn, UpdateDateColumn } from 'typeorm';
import { ClaimEntity } from '../../claim/entities';
import { ClaimEvidenceAggregate } from '../models';

@VsolvEntity({ name: 'claim_evidence' }, 'tenant')
export class ClaimEvidenceEntity {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true })
  referenceId!: string | null;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  claimId!: string;

  @JoinColumn({ name: 'claimId' })
  @ManyToOne(() => ClaimEntity)
  claim?: ClaimEntity;

  toAggregate(publisher?: EventPublisher): ClaimEvidenceAggregate {
    return mergeObjectContext(
      new ClaimEvidenceAggregate({
        id: this.id,
        referenceId: this.referenceId,

        created: this.created,
        modified: this.modified,
      }),
      publisher
    );
  }
}
